package main

import (
	"fmt"
	"log"
	"os"
	"os/exec"
	"strings"
	"time"

	"github.com/apt-defender/helper-v2/internal/api"
	"github.com/apt-defender/helper-v2/internal/config"
)

func main() {
	// Setup logging to both file and console
	logFile, err := os.OpenFile("apt-defender-v2.log", os.O_RDWR|os.O_CREATE|os.O_APPEND, 0666)
	if err == nil {
		defer logFile.Close()
	}

	printBanner()
	log.Println("=== APT Defender Helper v2.0 Starting ===")
	fmt.Println("✅ APT Defender Helper v2.0 Starting...")

	// Load configuration
	cfgPath := config.GetConfigPath()
	cfg, err := config.Load(cfgPath)
	if err != nil {
		log.Printf("Config load error: %v, using defaults", err)
		fmt.Printf("⚠️  Config not found, using defaults\n")
		cfg = config.DefaultConfig()

		// Try to save default config
		if err := cfg.Save(cfgPath); err != nil {
			log.Printf("Warning: Could not save default config: %v", err)
		} else {
			fmt.Printf("✅ Default config saved to: %s\n", cfgPath)
		}
	} else {
		fmt.Printf("✅ Configuration loaded from: %s\n", cfgPath)
	}

	log.Printf("Configuration: Host=%s Port=%d", cfg.Host, cfg.Port)

	// Print service info
	fmt.Println("\n" + strings.Repeat("=", 60))
	fmt.Println("📡 API SERVER INFORMATION")
	fmt.Println(strings.Repeat("=", 60))
	fmt.Printf("  Address:     http://%s:%d\n", cfg.Host, cfg.Port)
	fmt.Printf("  Auth Token:  %s\n", cfg.AuthToken)
	fmt.Println(strings.Repeat("=", 60))

	fmt.Println("\n🔹 AVAILABLE FEATURES:")
	fmt.Println("  • File Scanning (EICAR detection, hash-based)")
	fmt.Println("  • Remote PC Shutdown/Restart")
	fmt.Println("  • Workstation Lock")
	fmt.Println("  • File Locking (read-only protection)")
	fmt.Println("  • Network Blocking (Windows Firewall control)")
	fmt.Println("  • Application Network Blocking")
	fmt.Println(strings.Repeat("=", 60))

	fmt.Println("\n📡 Starting API Server...")
	fmt.Println("⏳ Waiting for commands from Pi Agent...")
	fmt.Println("\n🌐 Dashboard URL: http://localhost:" + fmt.Sprintf("%d", cfg.Port) + "/dashboard")
	fmt.Println("   Opening dashboard in browser...\n")

	// Start API server in background
	server := api.New(cfg)
	go func() {
		if err := server.Start(); err != nil {
			log.Fatalf("Server error: %v", err)
		}
	}()

	// Wait for server to start
	time.Sleep(1 * time.Second)

	// Open dashboard in default browser
	dashboardURL := fmt.Sprintf("http://localhost:%d/dashboard", cfg.Port)
	openBrowser(dashboardURL)
	// Keep program running
	fmt.Println("\n✅ Server is running. Press Ctrl+C to exit.")
	select {} // Block forever
}

func printBanner() {
	banner := `
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║        APT DEFENDER HELPER SERVICE v2.0                 ║
║        Advanced PC Protection & Remote Control          ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
`
	fmt.Println(banner)
}

func openBrowser(url string) {
	cmd := exec.Command("rundll32", "url.dll,FileProtocolHandler", url)
	if err := cmd.Start(); err != nil {
		log.Printf("Failed to open browser: %v", err)
		fmt.Println("⚠️  Could not open browser automatically. Please open manually:")
		fmt.Println("   " + url)
	}
}
