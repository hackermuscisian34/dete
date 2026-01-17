package server

import (
	"crypto/tls"
	"crypto/x509"
	"fmt"
	"io/ioutil"
	"log"
	"net/http"
	"time"

	"github.com/gorilla/mux"
	"github.com/apt-defender/helper-service/internal/config"
	"github.com/apt-defender/helper-service/internal/handlers"
)

// Server represents the HTTP server
type Server struct {
	config  *config.Config
	router *mux.Router
}

// New creates a new server instance
func New(cfg *config.Config) *Server {
	router := mux.NewRouter()
	
	srv := &Server{
		config: cfg,
		router: router,
	}
	
	srv.setupRoutes()
	
	return srv
}

// setupRoutes configures all API routes
func (s *Server) setupRoutes() {
	// Add logging middleware
	s.router.Use(loggingMiddleware)
	
	// Add rate limiting middleware
	s.router.Use(rateLimitMiddleware(s.config.RateLimit))
	
	// API v1 routes
	v1 := s.router.PathPrefix("/v1").Subrouter()
	
	// Health check
	v1.HandleFunc("/health", handlers.HealthCheck).Methods("GET")
	
	// Process management
	v1.HandleFunc("/processes", handlers.GetProcesses).Methods("GET")
	v1.HandleFunc("/process/kill", handlers.KillProcess).Methods("POST")
	
	// File operations
	v1.HandleFunc("/files/hash", handlers.GetFileHash).Methods("GET")
	v1.HandleFunc("/file/quarantine", handlers.QuarantineFile).Methods("POST")
	
	// Network operations
	v1.HandleFunc("/network/connections", handlers.GetNetworkConnections).Methods("GET")
	v1.HandleFunc("/network/disable", handlers.DisableNetwork).Methods("POST")
	
	// System operations
	v1.HandleFunc("/system/lock", handlers.LockSystem).Methods("POST")
	v1.HandleFunc("/system/shutdown", handlers.ShutdownSystem).Methods("POST")
	
	// Persistence check
	v1.HandleFunc("/persistence", handlers.GetPersistence).Methods("GET")
}

// Start starts the HTTPS server
func (s *Server) Start() error {
	addr := fmt.Sprintf("%s:%d", s.config.Host, s.config.Port)
	
	// Create TLS configuration for mTLS
	tlsConfig := &tls.Config{
		MinVersion: tls.VersionTLS13,
		ClientAuth: tls.NoClientCert, // Default to no cert
	}

	if s.config.EnableMTLS {
		// Load CA cert (or use the server cert as CA if self-signed peer)
		caCert, err := ioutil.ReadFile(s.config.CertFile)
		if err != nil {
			return fmt.Errorf("failed to read CA cert: %v", err)
		}
		
		caCertPool := x509.NewCertPool()
		caCertPool.AppendCertsFromPEM(caCert)
		
		tlsConfig.ClientCAs = caCertPool
		tlsConfig.ClientAuth = tls.RequireAndVerifyClientCert
		log.Printf("🔒 mTLS Enabled: Only trusted Pi connections allowed")
	}

	server := &http.Server{
		Addr:         addr,
		Handler:      s.router,
		ReadTimeout:  15 * time.Second,
		WriteTimeout: 15 * time.Second,
		IdleTimeout:  60 * time.Second,
		TLSConfig:    tlsConfig,
	}
	
	// Start HTTPS server
	log.Printf("✅ APT Defender Helper Ready")
	return server.ListenAndServeTLS(s.config.CertFile, s.config.KeyFile)
}

// loggingMiddleware logs all requests
func loggingMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		start := time.Now()
		log.Printf("%s %s from %s", r.Method, r.URL.Path, r.RemoteAddr)
		
		next.ServeHTTP(w, r)
		
		log.Printf("%s %s completed in %v", r.Method, r.URL.Path, time.Since(start))
	})
}

// rateLimitMiddleware implements simple rate limiting
func rateLimitMiddleware(maxPerMinute int) mux.MiddlewareFunc {
	// TODO: Implement proper rate limiting with token bucket
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			// For now, just pass through
			next.ServeHTTP(w, r)
		})
	}
}
