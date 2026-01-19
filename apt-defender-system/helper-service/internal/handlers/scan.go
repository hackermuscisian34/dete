package handlers

import (
	"crypto/sha256"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
	"os/user"
	"path/filepath"
	"sync"
	"time"
)

type ScanStatus struct {
	Active        bool      `json:"active"`
	TotalFiles    int64     `json:"total_files"`
	ScannedFiles  int64     `json:"scanned_files"`
	ThreatsFound  int       `json:"threats_found"`
	StartTime     time.Time `json:"start_time"`
	CurrentFolder string    `json:"current_folder"`
	ScanType      string    `json:"scan_type"`
}

var (
	currentScan *ScanStatus
	scanMutex   sync.Mutex
)

// StartScan triggers a background file system scan
func StartScan(w http.ResponseWriter, r *http.Request) {
	scanMutex.Lock()
	if currentScan != nil && currentScan.Active {
		scanMutex.Unlock()
		sendError(w, http.StatusConflict, "A scan is already in progress")
		return
	}

	var req struct {
		ScanType string `json:"scan_type"`
	}
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		req.ScanType = "full"
	}

	currentScan = &ScanStatus{
		Active:    true,
		StartTime: time.Now(),
		ScanType:  req.ScanType,
	}
	scanMutex.Unlock()

	// Run scan in background
	go runBackgroundScan()

	response := Response{
		Success: true,
		Data:    currentScan,
	}
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}

// GetScanStatus returns the current progress of the scan
func GetScanStatus(w http.ResponseWriter, r *http.Request) {
	scanMutex.Lock()
	defer scanMutex.Unlock()

	if currentScan == nil {
		sendError(w, http.StatusNotFound, "No scan history available")
		return
	}

	response := Response{
		Success: true,
		Data:    currentScan,
	}
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}

func runBackgroundScan() {
	u, err := user.Current()
	if err != nil {
		log.Printf("Scan Error: Could not get current user: %v", err)
		return
	}

	folders := []string{
		filepath.Join(u.HomeDir, "Downloads"),
		filepath.Join(u.HomeDir, "Documents"),
		filepath.Join(u.HomeDir, "Desktop"),
	}

	// First pass: Count files for progress bar
	for _, folder := range folders {
		filepath.Walk(folder, func(path string, info os.FileInfo, err error) error {
			if err == nil && !info.IsDir() {
				currentScan.TotalFiles++
			}
			return nil
		})
	}

	// Second pass: Scan files
	for _, folder := range folders {
		currentScan.CurrentFolder = folder
		filepath.Walk(folder, func(path string, info os.FileInfo, err error) error {
			if !currentScan.Active {
				return filepath.SkipDir // Stop if cancelled (implementation for cancel could be added)
			}
			if err != nil || info.IsDir() {
				return nil
			}

			// Simulate deep scan work (check hash, etc.)
			scanFile(path)

			currentScan.ScannedFiles++
			// Slow down a bit so user can actually see progress in UI
			time.Sleep(10 * time.Millisecond)
			return nil
		})
	}

	currentScan.Active = false
	currentScan.CurrentFolder = "Complete"
	log.Printf("Scan complete: %d files scanned, %d threats found", currentScan.ScannedFiles, currentScan.ThreatsFound)
}

func scanFile(path string) {
	// 1. Basic extension check for highly suspicious items
	ext := filepath.Ext(path)
	suspiciousExts := map[string]bool{
		".exe": true, ".bat": true, ".ps1": true, ".vbs": true, ".js": true,
	}

	if suspiciousExts[ext] {
		// Calculate hash for suspicious files
		f, err := os.Open(path)
		if err == nil {
			defer f.Close()
			h := sha256.New()
			if _, err := io.Copy(h, f); err == nil {
				hash := fmt.Sprintf("%x", h.Sum(nil))
				// Simple mock threat matching (in real life, check against DB)
				if hash == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855" { // Sample hash
					currentScan.ThreatsFound++
				}
			}
		}
	}
}
