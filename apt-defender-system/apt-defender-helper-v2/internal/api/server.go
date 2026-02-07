package api

import (
	"encoding/json"
	"fmt"
	"log"
	"net/http"

	"github.com/apt-defender/helper-v2/internal/config"
	"github.com/apt-defender/helper-v2/internal/control"
	"github.com/apt-defender/helper-v2/internal/dashboard"
	"github.com/apt-defender/helper-v2/internal/scanner"
	"github.com/apt-defender/helper-v2/internal/telemetry"
)

type Server struct {
	config  *config.Config
	scanner *scanner.Scanner
}

type Response struct {
	Success bool        `json:"success"`
	Data    interface{} `json:"data,omitempty"`
	Error   string      `json:"error,omitempty"`
}

func New(cfg *config.Config) *Server {
	return &Server{
		config:  cfg,
		scanner: scanner.New(cfg.ScanPaths),
	}
}

func (s *Server) Start() error {
	// Dashboard (no auth required)
	http.HandleFunc("/", s.handleDashboard)
	http.HandleFunc("/dashboard", s.handleDashboard)

	// Setup routes
	http.HandleFunc("/api/v1/health", s.handleHealth)
	http.HandleFunc("/api/v1/telemetry", s.handleTelemetry)

	// Scanner endpoints
	http.HandleFunc("/api/v1/scan/start", s.authMiddleware(s.handleScanStart))
	http.HandleFunc("/api/v1/scan/status", s.authMiddleware(s.handleScanStatus))
	http.HandleFunc("/api/v1/scan/stop", s.authMiddleware(s.handleScanStop))

	// System control endpoints
	http.HandleFunc("/api/v1/system/shutdown", s.authMiddleware(s.handleShutdown))
	http.HandleFunc("/api/v1/system/restart", s.authMiddleware(s.handleRestart))
	http.HandleFunc("/api/v1/system/lock", s.authMiddleware(s.handleLock))

	// File control endpoints
	http.HandleFunc("/api/v1/files/lock", s.authMiddleware(s.handleFileLock))
	http.HandleFunc("/api/v1/files/unlock", s.authMiddleware(s.handleFileUnlock))

	// Network control endpoints
	http.HandleFunc("/api/v1/network/block", s.authMiddleware(s.handleNetworkBlock))
	http.HandleFunc("/api/v1/network/unblock", s.authMiddleware(s.handleNetworkUnblock))
	http.HandleFunc("/api/v1/network/status", s.authMiddleware(s.handleNetworkStatus))
	http.HandleFunc("/api/v1/network/block-app", s.authMiddleware(s.handleBlockApp))

	// System info endpoint (no auth needed for local dashboard)
	http.HandleFunc("/api/v1/system/info", s.handleSystemInfo)

	// Registration notification endpoint (for Pi Agent to tell PC it's been added)
	http.HandleFunc("/api/v1/register-notification", s.authMiddleware(s.handleRegistrationNotification))

	addr := fmt.Sprintf("%s:%d", s.config.Host, s.config.Port)
	log.Printf("🚀 Starting HTTP server on %s", addr)
	log.Printf("✅ APT Defender Helper v2.0 Ready")

	return http.ListenAndServe(addr, nil)
}

// authMiddleware validates the auth token
func (s *Server) authMiddleware(next http.HandlerFunc) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		token := r.Header.Get("Authorization")
		if token != "Bearer "+s.config.AuthToken {
			s.sendError(w, http.StatusUnauthorized, "Unauthorized")
			return
		}
		next(w, r)
	}
}

func (s *Server) sendJSON(w http.ResponseWriter, data interface{}) {
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(Response{Success: true, Data: data})
}

func (s *Server) sendError(w http.ResponseWriter, statusCode int, message string) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(statusCode)
	json.NewEncoder(w).Encode(Response{Success: false, Error: message})
}

// Health check
func (s *Server) handleHealth(w http.ResponseWriter, r *http.Request) {
	s.sendJSON(w, map[string]string{"status": "healthy", "version": "2.0"})
}

// Scanner handlers
func (s *Server) handleScanStart(w http.ResponseWriter, r *http.Request) {
	var req struct {
		ScanType string `json:"scan_type"`
	}
	json.NewDecoder(r.Body).Decode(&req)

	if req.ScanType == "" {
		req.ScanType = "full"
	}

	if err := s.scanner.StartScan(req.ScanType); err != nil {
		s.sendError(w, http.StatusConflict, err.Error())
		return
	}

	s.sendJSON(w, s.scanner.GetStatus())
}

func (s *Server) handleScanStatus(w http.ResponseWriter, r *http.Request) {
	s.sendJSON(w, s.scanner.GetStatus())
}

func (s *Server) handleScanStop(w http.ResponseWriter, r *http.Request) {
	s.scanner.StopScan()
	s.sendJSON(w, map[string]string{"message": "Scan stopped"})
}

// System control handlers
func (s *Server) handleShutdown(w http.ResponseWriter, r *http.Request) {
	log.Println("⚠️ SHUTDOWN REQUEST RECEIVED FROM PI AGENT")
	s.sendJSON(w, map[string]string{"message": "Shutdown initiated"})

	// Shutdown in goroutine to allow response to be sent
	go func() {
		if err := control.ShutdownPC(); err != nil {
			log.Printf("Shutdown error: %v", err)
		}
	}()
}

func (s *Server) handleRestart(w http.ResponseWriter, r *http.Request) {
	log.Println("⚠️ RESTART REQUEST RECEIVED FROM PI AGENT")
	s.sendJSON(w, map[string]string{"message": "Restart initiated"})

	go func() {
		if err := control.RestartPC(); err != nil {
			log.Printf("Restart error: %v", err)
		}
	}()
}

func (s *Server) handleLock(w http.ResponseWriter, r *http.Request) {
	log.Println("🔒 LOCK REQUEST RECEIVED FROM PI AGENT")

	if err := control.LockWorkstation(); err != nil {
		s.sendError(w, http.StatusInternalServerError, err.Error())
		return
	}

	s.sendJSON(w, map[string]string{"message": "Workstation locked"})
}

// File control handlers
func (s *Server) handleFileLock(w http.ResponseWriter, r *http.Request) {
	var req struct {
		Path string `json:"path"`
	}
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		s.sendError(w, http.StatusBadRequest, "Invalid request")
		return
	}

	if err := control.LockFile(req.Path); err != nil {
		s.sendError(w, http.StatusInternalServerError, err.Error())
		return
	}

	s.sendJSON(w, map[string]string{"message": "File locked", "path": req.Path})
}

func (s *Server) handleFileUnlock(w http.ResponseWriter, r *http.Request) {
	var req struct {
		Path string `json:"path"`
	}
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		s.sendError(w, http.StatusBadRequest, "Invalid request")
		return
	}

	if err := control.UnlockFile(req.Path); err != nil {
		s.sendError(w, http.StatusInternalServerError, err.Error())
		return
	}

	s.sendJSON(w, map[string]string{"message": "File unlocked", "path": req.Path})
}

// Network control handlers
func (s *Server) handleNetworkBlock(w http.ResponseWriter, r *http.Request) {
	log.Println("🚫 NETWORK BLOCK REQUEST RECEIVED FROM PI AGENT")

	if err := control.BlockAllNetwork(); err != nil {
		s.sendError(w, http.StatusInternalServerError, err.Error())
		return
	}

	s.sendJSON(w, map[string]string{"message": "Network access blocked"})
}

func (s *Server) handleNetworkUnblock(w http.ResponseWriter, r *http.Request) {
	log.Println("✅ NETWORK UNBLOCK REQUEST RECEIVED FROM PI AGENT")

	if err := control.UnblockAllNetwork(); err != nil {
		s.sendError(w, http.StatusInternalServerError, err.Error())
		return
	}

	s.sendJSON(w, map[string]string{"message": "Network access restored"})
}

func (s *Server) handleNetworkStatus(w http.ResponseWriter, r *http.Request) {
	blocked, err := control.GetNetworkStatus()
	if err != nil {
		s.sendError(w, http.StatusInternalServerError, err.Error())
		return
	}

	s.sendJSON(w, map[string]interface{}{
		"blocked": blocked,
		"status":  map[bool]string{true: "blocked", false: "open"}[blocked],
	})
}

func (s *Server) handleBlockApp(w http.ResponseWriter, r *http.Request) {
	var req struct {
		Path string `json:"path"`
	}
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		s.sendError(w, http.StatusBadRequest, "Invalid request")
		return
	}

	if err := control.BlockApplication(req.Path); err != nil {
		s.sendError(w, http.StatusInternalServerError, err.Error())
		return
	}

	s.sendJSON(w, map[string]string{"message": "Application blocked", "path": req.Path})
}

// Dashboard handler
func (s *Server) handleDashboard(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "text/html; charset=utf-8")
	w.Write([]byte(dashboard.HTML))
}

// Telemetry handler
func (s *Server) handleTelemetry(w http.ResponseWriter, r *http.Request) {
	stats, err := telemetry.GetSystemStats()
	if err != nil {
		s.sendError(w, http.StatusInternalServerError, err.Error())
		return
	}

	s.sendJSON(w, stats)
}

// System info handler (includes IP addresses)
func (s *Server) handleSystemInfo(w http.ResponseWriter, r *http.Request) {
	ips := telemetry.GetLocalIPs()

	s.sendJSON(w, map[string]interface{}{
		"ip_addresses":       ips,
		"registered_with_pi": s.config.RegisteredWithPi,
		"pi_agent_ip":        s.config.PiAgentIP,
	})
}
