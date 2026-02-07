package scanner

import (
	"crypto/sha256"
	"fmt"
	"io"
	"log"
	"os"
	"path/filepath"
	"strings"
	"sync"
	"sync/atomic"
	"time"
)

type ScanStatus struct {
	Active        bool      `json:"active"`
	TotalFiles    int64     `json:"total_files"`
	ScannedFiles  int64     `json:"scanned_files"`
	ThreatsFound  int       `json:"threats_found"`
	Threats       []Threat  `json:"threats"`
	StartTime     time.Time `json:"start_time"`
	CurrentFolder string    `json:"current_folder"`
	ScanType      string    `json:"scan_type"`
}

type Threat struct {
	Path       string    `json:"path"`
	Type       string    `json:"type"`
	Signature  string    `json:"signature"`
	DetectedAt time.Time `json:"detected_at"`
}

type Scanner struct {
	status     *ScanStatus
	mutex      sync.RWMutex
	scanPaths  []string
	stopSignal chan struct{}
}

func New(scanPaths []string) *Scanner {
	return &Scanner{
		scanPaths: scanPaths,
		status: &ScanStatus{
			Active:  false,
			Threats: []Threat{},
		},
	}
}

func (s *Scanner) GetStatus() *ScanStatus {
	s.mutex.RLock()
	defer s.mutex.RUnlock()

	statusCopy := *s.status
	threatsCopy := make([]Threat, len(s.status.Threats))
	copy(threatsCopy, s.status.Threats)
	statusCopy.Threats = threatsCopy

	return &statusCopy
}

func (s *Scanner) StartScan(scanType string) error {
	s.mutex.Lock()
	if s.status.Active {
		s.mutex.Unlock()
		return fmt.Errorf("scan already in progress")
	}

	s.status = &ScanStatus{
		Active:    true,
		StartTime: time.Now(),
		ScanType:  scanType,
		Threats:   []Threat{},
	}
	s.stopSignal = make(chan struct{})
	s.mutex.Unlock()

	go s.runScan()
	return nil
}

func (s *Scanner) StopScan() {
	s.mutex.Lock()
	defer s.mutex.Unlock()

	if s.status.Active && s.stopSignal != nil {
		close(s.stopSignal)
	}
}

func (s *Scanner) runScan() {
	defer func() {
		s.mutex.Lock()
		s.status.Active = false
		s.status.CurrentFolder = "Complete"
		s.mutex.Unlock()
		log.Printf("Scan complete: %d files scanned, %d threats found",
			s.status.ScannedFiles, s.status.ThreatsFound)
	}()

	// First pass: count files
	for _, folder := range s.scanPaths {
		filepath.Walk(folder, func(path string, info os.FileInfo, err error) error {
			if err == nil && !info.IsDir() {
				atomic.AddInt64(&s.status.TotalFiles, 1)
			}
			return nil
		})
	}

	// Second pass: scan files
	for _, folder := range s.scanPaths {
		select {
		case <-s.stopSignal:
			return
		default:
		}

		s.mutex.Lock()
		s.status.CurrentFolder = folder
		s.mutex.Unlock()

		filepath.Walk(folder, func(path string, info os.FileInfo, err error) error {
			select {
			case <-s.stopSignal:
				return filepath.SkipAll
			default:
			}

			if err != nil || info.IsDir() {
				return nil
			}

			// Scan the file
			if threat := s.scanFile(path); threat != nil {
				s.mutex.Lock()
				s.status.Threats = append(s.status.Threats, *threat)
				s.status.ThreatsFound++
				s.mutex.Unlock()
				log.Printf("THREAT DETECTED: %s [%s]", path, threat.Type)
			}

			atomic.AddInt64(&s.status.ScannedFiles, 1)
			time.Sleep(5 * time.Millisecond) // Slow down to see progress
			return nil
		})
	}
}

func (s *Scanner) scanFile(path string) *Threat {
	ext := strings.ToLower(filepath.Ext(path))
	basename := strings.ToLower(filepath.Base(path))

	// Suspicious extensions
	suspiciousExts := map[string]bool{
		".exe": true, ".bat": true, ".ps1": true, ".vbs": true,
		".js": true, ".com": true, ".scr": true, ".cmd": true,
		".msi": true, ".dll": true,
	}

	// Open file for analysis
	if suspiciousExts[ext] || basename == "eicar.com" || basename == "eicar.txt" {
		f, err := os.Open(path)
		if err != nil {
			return nil
		}
		defer f.Close()

		// Read first 1KB for signature check
		buf := make([]byte, 1024)
		n, _ := f.Read(buf)
		content := string(buf[:n])

		// EICAR Standard Test String Check
		if containsEicar(content) {
			return &Threat{
				Path:       path,
				Type:       "Malware.Test.EICAR",
				Signature:  "EICAR-STANDARD-ANTIVIRUS-TEST-FILE",
				DetectedAt: time.Now(),
			}
		}

		// Hash-based detection for known threats
		f.Seek(0, 0)
		h := sha256.New()
		if _, err := io.Copy(h, f); err == nil {
			hash := fmt.Sprintf("%x", h.Sum(nil))

			// Known malicious hashes (add more as needed)
			knownThreats := map[string]string{
				"44d88612fea8a8f36de82e1278abb02f":                                 "Malware.Generic.Hash",
				"275a021bbfb6489e54d471899f7db9d1663fc695ec2fe2a2c4538aabf651fd0f": "Malware.EICAR.SHA256",
			}

			if threatType, found := knownThreats[hash]; found {
				return &Threat{
					Path:       path,
					Type:       threatType,
					Signature:  hash,
					DetectedAt: time.Now(),
				}
			}
		}
	}

	return nil
}

func containsEicar(s string) bool {
	eicarSignature := "X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*"
	return strings.Contains(s, eicarSignature)
}
