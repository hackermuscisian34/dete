package api

import (
	"encoding/json"
	"log"
	"net/http"

	"github.com/apt-defender/helper-v2/internal/config"
)

type RegistrationNotification struct {
	PiAgentIP  string `json:"pi_agent_ip"`
	Registered bool   `json:"registered"`
}

// HandleRegistrationNotification receives notification from Pi Agent that PC has been registered
func (s *Server) handleRegistrationNotification(w http.ResponseWriter, r *http.Request) {
	var notification RegistrationNotification

	if err := json.NewDecoder(r.Body).Decode(&notification); err != nil {
		s.sendError(w, http.StatusBadRequest, "Invalid request")
		return
	}

	log.Printf("📡 Received registration notification from Pi Agent at %s", notification.PiAgentIP)

	// Update config
	s.config.RegisteredWithPi = notification.Registered
	s.config.PiAgentIP = notification.PiAgentIP

	// Save config to disk
	if err := s.config.Save(config.GetConfigPath()); err != nil {
		log.Printf("⚠️ Failed to save config after registration: %v", err)
		// Don't fail the request, just log the error
	}

	log.Printf("✅ PC registered with Pi Agent at %s", notification.PiAgentIP)

	s.sendJSON(w, map[string]string{
		"message": "Registration acknowledged",
		"status":  "connected",
	})
}
