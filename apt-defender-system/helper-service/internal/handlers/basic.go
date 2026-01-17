package handlers

import (
	"encoding/json"
	"net/http"
	"runtime"
	
	"github.com/shirou/gopsutil/v3/process"
	"github.com/shirou/gopsutil/v3/net"
)

// Response structs
type Response struct {
	Success bool        `json:"success"`
	Data    interface{} `json:"data,omitempty"`
	Error   string      `json:"error,omitempty"`
}

type HealthResponse struct {
	Status  string `json:"status"`
	Version string `json:"version"`
	Uptime  int64  `json:"uptime"`
	OS      string `json:"os"`
}

type ProcessInfo struct {
	PID   int32  `json:"pid"`
	Name  string `json:"name"`
	Path  string `json:"path"`
	User  string `json:"user"`
}

type ConnectionInfo struct {
	LocalIP  string `json:"local_ip"`
	RemoteIP string `json:"remote_ip"`
	LocalPort uint32 `json:"local_port"`
	RemotePort uint32 `json:"remote_port"`
	Protocol string `json:"protocol"`
	State    string `json:"state"`
}

// HealthCheck returns service health status
func HealthCheck(w http.ResponseWriter, r *http.Request) {
	response := Response{
		Success: true,
		Data: HealthResponse{
			Status:  "healthy",
			Version: "1.0.0",
			Uptime:  0, // TODO: Calculate actual uptime
			OS:      runtime.GOOS,
		},
	}
	
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}

// GetProcesses returns list of running processes
func GetProcesses(w http.ResponseWriter, r *http.Request) {
	processes, err := process.Processes()
	if err != nil {
		sendError(w, http.StatusInternalServerError, err.Error())
		return
	}
	
	var processList []ProcessInfo
	
	for _, p := range processes {
		name, _ := p.Name()
		exe, _ := p.Exe()
		username, _ := p.Username()
		
		processList = append(processList, ProcessInfo{
			PID:  p.Pid,
			Name: name,
			Path: exe,
			User: username,
		})
	}
	
	response := Response{
		Success: true,
		Data: map[string]interface{}{
			"processes": processList,
		},
	}
	
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}

// GetNetworkConnections returns active network connections
func GetNetworkConnections(w http.ResponseWriter, r *http.Request) {
	connections, err := net.Connections("all")
	if err != nil {
		sendError(w, http.StatusInternalServerError, err.Error())
		return
	}
	
	var connList []ConnectionInfo
	
	for _, conn := range connections {
		connList = append(connList, ConnectionInfo{
			LocalIP:    conn.Laddr.IP,
			RemoteIP:   conn.Raddr.IP,
			LocalPort:  conn.Laddr.Port,
			RemotePort: conn.Raddr.Port,
			Protocol:   protocolName(conn.Type),
			State:      conn.Status,
		})
	}
	
	response := Response{
		Success: true,
		Data: map[string]interface{}{
			"connections": connList,
		},
	}
	
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}

// Helper functions
func sendError(w http.ResponseWriter, code int, message string) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(code)
	
	response := Response{
		Success: false,
		Error:   message,
	}
	
	json.NewEncoder(w).Encode(response)
}

func protocolName(sockType uint32) string {
	switch sockType {
	case 1:
		return "TCP"
	case 2:
		return "UDP"
	default:
		return "OTHER"
	}
}
