package handlers

import (
	"crypto/sha256"
	"encoding/base64"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"path/filepath"
	"runtime"
	
	"github.com/shirou/gopsutil/v3/process"
)

type KillProcessRequest struct {
	PID int32 `json:"pid"`
}

type QuarantineFileRequest struct {
	Path   string `json:"path"`
	Reason string `json:"reason"`
}

type ShutdownRequest struct {
	DelaySeconds int `json:"delay_seconds"`
}

// KillProcess terminates a process by PID
func KillProcess(w http.ResponseWriter, r *http.Request) {
	var req KillProcessRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		sendError(w, http.StatusBadRequest, "Invalid request")
		return
	}
	
	p, err := process.NewProcess(req.PID)
	if err != nil {
		sendError(w, http.StatusNotFound, fmt.Sprintf("Process %d not found", req.PID))
		return
	}
	
	err = p.Kill()
	if err != nil {
		sendError(w, http.StatusInternalServerError, fmt.Sprintf("Failed to kill process: %v", err))
		return
	}
	
	response := Response{
		Success: true,
		Data: map[string]interface{}{
			"pid": req.PID,
			"message": "Process terminated successfully",
		},
	}
	
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}

// GetFileHash calculates SHA256 hash of file
func GetFileHash(w http.ResponseWriter, r *http.Request) {
	// Path is base64 encoded in query parameter
	encodedPath := r.URL.Query().Get("path")
	if encodedPath == "" {
		sendError(w, http.StatusBadRequest, "Missing path parameter")
		return
	}
	
	pathBytes, err := base64.StdEncoding.DecodeString(encodedPath)
	if err != nil {
		sendError(w, http.StatusBadRequest, "Invalid path encoding")
		return
	}
	
	filePath := string(pathBytes)
	
	// Calculate hash
	file, err := os.Open(filePath)
	if err != nil {
		sendError(w, http.StatusNotFound, fmt.Sprintf("File not found: %s", filePath))
		return
	}
	defer file.Close()
	
	hasher := sha256.New()
	if _, err := io.Copy(hasher, file); err != nil {
		sendError(w, http.StatusInternalServerError, "Failed to hash file")
		return
	}
	
	hash := fmt.Sprintf("%x", hasher.Sum(nil))
	
	response := Response{
		Success: true,
		Data: map[string]interface{}{
			"path":   filePath,
			"sha256": hash,
		},
	}
	
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}

// QuarantineFile moves file to quarantine directory
func QuarantineFile(w http.ResponseWriter, r *http.Request) {
	var req QuarantineFileRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		sendError(w, http.StatusBadRequest, "Invalid request")
		return
	}
	
	// Quarantine directory
	var quarantineDir string
	if runtime.GOOS == "windows" {
		quarantineDir = "C:\\ProgramData\\APTDefender\\quarantine"
	} else {
		quarantineDir = "/var/lib/apt-defender/quarantine"
	}
	
	// Ensure quarantine directory exists
	os.MkdirAll(quarantineDir, 0700)
	
	// Generate quarantine filename (preserve original name + timestamp)
	fileName := filepath.Base(req.Path)
	quarantinePath := filepath.Join(quarantineDir, fileName)
	
	// Move file
	err := os.Rename(req.Path, quarantinePath)
	if err != nil {
		// Try copy if rename fails (cross-device)
		err = copyFile(req.Path, quarantinePath)
		if err != nil {
			sendError(w, http.StatusInternalServerError, fmt.Sprintf("Failed to quarantine: %v", err))
			return
		}
		os.Remove(req.Path)
	}
	
	response := Response{
		Success: true,
		Data: map[string]interface{}{
			"original_path":   req.Path,
			"quarantine_path": quarantinePath,
			"reason":          req.Reason,
		},
	}
	
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}

// DisableNetwork disables all network adapters
func DisableNetwork(w http.ResponseWriter, r *http.Request) {
	// Platform-specific implementation needed
	var err error
	
	if runtime.GOOS == "windows" {
		// Windows: netsh interface set interface "Ethernet" admin=disable
		// TODO: Implement for all adapters
		err = fmt.Errorf("not implemented for Windows")
	} else {
		// Linux: ip link set <interface> down
		// TODO: Implement for all interfaces
		err = fmt.Errorf("not implemented for Linux")
	}
	
	if err != nil {
		sendError(w, http.StatusInternalServerError, err.Error())
		return
	}
	
	response := Response{
		Success: true,
		Data: map[string]interface{}{
			"message": "Network disabled",
		},
	}
	
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}

// LockSystem locks the screen
func LockSystem(w http.ResponseWriter, r *http.Request) {
	var err error
	
	if runtime.GOOS == "windows" {
		// Windows: rundll32.exe user32.dll,LockWorkStation
		// TODO: Implement
		err = fmt.Errorf("not implemented for Windows")
	} else {
		// Linux: loginctl lock-session
		// TODO: Implement
		err = fmt.Errorf("not implemented for Linux")
	}
	
	if err != nil {
		sendError(w, http.StatusInternalServerError, err.Error())
		return
	}
	
	response := Response{
		Success: true,
		Data: map[string]interface{}{
			"message": "System locked",
		},
	}
	
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}

// ShutdownSystem shuts down the system
func ShutdownSystem(w http.ResponseWriter, r *http.Request) {
	var req ShutdownRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		req.DelaySeconds = 60 // Default
	}
	
	// Platform-specific shutdown
	var err error
	
	if runtime.GOOS == "windows" {
		// Windows: shutdown /s /t <seconds>
		// TODO: Implement
		err = fmt.Errorf("not implemented for Windows")
	} else {
		// Linux: shutdown -h +<minutes>
		// TODO: Implement
		err = fmt.Errorf("not implemented for Linux")
	}
	
	if err != nil {
		sendError(w, http.StatusInternalServerError, err.Error())
		return
	}
	
	response := Response{
		Success: true,
		Data: map[string]interface{}{
			"message":       "Shutdown scheduled",
			"delay_seconds": req.DelaySeconds,
		},
	}
	
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}

// GetPersistence returns persistence mechanisms
func GetPersistence(w http.ResponseWriter, r *http.Request) {
	// TODO: Implement platform-specific persistence checks
	// Windows: Registry Run keys, Startup folder, Scheduled Tasks
	// Linux: cron, systemd, rc.local
	
	response := Response{
		Success: true,
		Data: map[string]interface{}{
			"entries": []interface{}{},
		},
	}
	
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}

// Helper function to copy file
func copyFile(src, dst string) error {
	sourceFile, err := os.Open(src)
	if err != nil {
		return err
	}
	defer sourceFile.Close()
	
	destFile, err := os.Create(dst)
	if err != nil {
		return err
	}
	defer destFile.Close()
	
	_, err = io.Copy(destFile, sourceFile)
	return err
}
