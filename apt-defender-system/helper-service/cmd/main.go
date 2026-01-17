package main

import (
	"fmt"
	"log"
	"os"

	"path/filepath"
	
	"github.com/apt-defender/helper-service/internal/server"
	"github.com/apt-defender/helper-service/internal/config"
	"github.com/lxn/walk"
	. "github.com/lxn/walk/declarative"
	"time"
	"syscall"
	"unsafe"
)

const (
	serviceName    = "APT Defender Helper"
	serviceVersion = "1.0.0"
)

var (
	user32           = syscall.NewLazyDLL("user32.dll")
	procMessageBoxW  = user32.NewProc("MessageBoxW")
)

func messageBox(title, text string, style uintptr) {
	titlePtr, _ := syscall.UTF16PtrFromString(title)
	textPtr, _ := syscall.UTF16PtrFromString(text)
	procMessageBoxW.Call(
		0,
		uintptr(unsafe.Pointer(textPtr)),
		uintptr(unsafe.Pointer(titlePtr)),
		style,
	)
}

func main() {
	// Setup file logging for debugging startup crashes
	logFile, _ := os.OpenFile("debug.log", os.O_RDWR|os.O_CREATE|os.O_APPEND, 0666)
	if logFile != nil {
		log.SetOutput(logFile)
	}
	defer logFile.Close()

	log.Println("Details: Application starting...")

	// Load configuration
	cfgPath := getConfigPath()
	cfg, err := config.Load(cfgPath)
	if err != nil {
		log.Printf("Config Error: %v", err)
		// We continue with defaults or show error in GUI if possible, 
		// but since we need config for server, we might fail later.
		// For now, let's try to show the GUI even if config fails so user sees error.
		if cfg == nil {
			cfg = &config.Config{Host: "0.0.0.0", Port: 7890} // Fallback
		}
	}

	var mw *walk.MainWindow
	var outTE *walk.TextEdit
	var statusLbl *walk.Label

	// Start server in background
	srv := server.New(cfg)
	go func() {
		// Small delay to let GUI load
		time.Sleep(1 * time.Second)
		
		logMsg := fmt.Sprintf("Starting HTTPS server on %s:%d\nCert: %s\n", cfg.Host, cfg.Port, cfg.CertFile)
		
		// Update GUI from background thread requires Synchronize
		if mw != nil {
			mw.Synchronize(func() {
				outTE.SetText(logMsg)
				statusLbl.SetText("RUNNING")
				// Bright Green for status
				statusLbl.SetTextColor(walk.RGB(0, 255, 0)) 
			})
		}

		if err := srv.Start(); err != nil {
			log.Printf("Server Start Error: %v", err)
			if mw != nil {
				mw.Synchronize(func() {
					outTE.SetText(outTE.Text() + "\nError: " + err.Error())
					statusLbl.SetText("ERROR")
					statusLbl.SetTextColor(walk.RGB(255, 0, 0)) // Red
				})
			}
		}
	}()

	// THEME COLORS - Professional Light Green (Modern/Clean)
	bgLight := walk.RGB(250, 255, 250)    // Very faint green/white
	accentGreen := walk.RGB(46, 204, 113) // Modern Flat Green (Emerald)
	darkText := walk.RGB(44, 62, 80)      // Midnight Blue/Dark
	grayText := walk.RGB(127, 140, 141)   // Concrete Gray
	white := walk.RGB(255, 255, 255)

	// Define GUI Layout
	if _, err := (MainWindow{
		AssignTo: &mw,
		Title:    serviceName,
		MinSize:  Size{400, 350},
		Size:     Size{500, 450},
		Layout:   VBox{Margins: Margins{20, 20, 20, 20}, Spacing: 15},
		// Clean Light Background
		Background: SolidColorBrush{Color: bgLight},
		Font: Font{Family: "Segoe UI", PointSize: 10}, 
		Children: []Widget{
			// Header Section
			Composite{
				Layout: VBox{Spacing: 5},
				Background: SolidColorBrush{Color: bgLight},
				Children: []Widget{
					Label{
						Text: "APT DEFENDER SYSTEM",
						Font: Font{PointSize: 18, Bold: true, Family: "Segoe UI"},
						TextColor: darkText,
						Background: SolidColorBrush{Color: bgLight},
					},
					Label{
						Text: "Trusted Device Security Agent",
						TextColor: grayText,
						Font: Font{PointSize: 9},
						Background: SolidColorBrush{Color: bgLight},
					},
				},
			},
			VSpacer{Size: 10},
			
			// Status Card
			Composite{
				Layout: HBox{Spacing: 10},
				Background: SolidColorBrush{Color: white},
				Children: []Widget{
					Label{
						Text: "STATUS:",
						Font: Font{Bold: true},
						TextColor: grayText,
						Background: SolidColorBrush{Color: white},
					},
					Label{
						AssignTo: &statusLbl,
						Text:     "INITIALIZING...",
						TextColor: walk.RGB(241, 196, 15), // Sunflower Yellow
						Font:     Font{PointSize: 11, Bold: true},
						Background: SolidColorBrush{Color: white},
					},
				},
			},
			
			Label{
				Text: fmt.Sprintf("Secure Endpoint: https://%s:%d", cfg.Host, cfg.Port),
				TextColor: accentGreen,
				Font: Font{PointSize: 9, Bold: true},
				Background: SolidColorBrush{Color: bgLight},
			},
			
			VSpacer{Size: 20},
			
			Label{
				Text: "Activity Log",
				TextColor: darkText,
				Font: Font{Bold: true},
				Background: SolidColorBrush{Color: bgLight},
			},
			
			// Modern Log Area (Clean White)
			TextEdit{
				AssignTo: &outTE,
				ReadOnly: true,
				VScroll:  true,
				TextColor:  darkText,
				Background: SolidColorBrush{Color: white},
				Font:       Font{Family: "Consolas", PointSize: 9},
				MinSize:    Size{0, 150},
			},
			
			VSpacer{Size: 10},
			
			PushButton{
				Text: "Minimize to Tray",
				OnClicked: func() {
					mw.Hide() // Hides window
				},
			},
		},
	}.Run()); err != nil {
		log.Printf("GUI Error: %v", err)
		// Fallback to message box if GUI fails
		messageBox("Startup Error", "Failed to open GUI: "+err.Error()+"\nCheck debug.log", 0x10)
	}
}


func getConfigPath() string {
	// Check environment variable first
	if path := os.Getenv("HELPER_CONFIG"); path != "" {
		return path
	}
	
	// Default locations
	if isWindows() {
		return "C:\\ProgramData\\APTDefender\\config.yaml"
	}
	return "/etc/apt-defender/config.yaml"
}

func isWindows() bool {
	return os.PathSeparator == '\\' && filepath.Separator == '\\'
}
