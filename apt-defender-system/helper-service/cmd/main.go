package main

import (
	"fmt"
	"log"
	"os"

	"bytes"
	"encoding/json"
	"net"
	"net/http"
	"syscall"
	"time"
	"unsafe"

	"github.com/apt-defender/helper-service/internal/config"
	"github.com/apt-defender/helper-service/internal/server"
	"github.com/lxn/walk"
	. "github.com/lxn/walk/declarative"
)

const (
	serviceName = "APT Defender Helper"
)

var (
	user32          = syscall.NewLazyDLL("user32.dll")
	procMessageBoxW = user32.NewProc("MessageBoxW")

	// GUI Pointers
	mw             *walk.MainWindow
	outTE          *walk.TextEdit
	statusLbl      *walk.Label
	ipEdit         *walk.LineEdit
	codeEdit       *walk.LineEdit
	pairBtn        *walk.PushButton
	disconnectBtn  *walk.PushButton
	pairingSection *walk.Composite
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
		if cfg == nil {
			cfg = &config.Config{Host: "0.0.0.0", Port: 7890} // Fallback
		}
	}

	// Always ensure we listen on all interfaces for the Pi Agent to connect
	if cfg.Host == "127.0.0.1" || cfg.Host == "localhost" {
		cfg.Host = "0.0.0.0"
	}

	log.Println("Details: Application starting...")

	// THEME COLORS
	bgLight := walk.RGB(250, 255, 250)
	accentGreen := walk.RGB(46, 204, 113)
	darkText := walk.RGB(44, 62, 80)
	grayText := walk.RGB(127, 140, 141)
	white := walk.RGB(255, 255, 255)

	// Start server in background
	srv := server.New(cfg)
	go func() {
		time.Sleep(1 * time.Second)
		ips := getAllLocalIPs()
		logMsg := fmt.Sprintf("Starting HTTPS server on %s:%d\nCert: %s\nDetected IPs: %v\n", cfg.Host, cfg.Port, cfg.CertFile, ips)
		if mw != nil {
			mw.Synchronize(func() {
				outTE.SetText(logMsg)
				if cfg.IsPaired {
					statusLbl.SetText("PAIRED & ACTIVE")
					statusLbl.SetTextColor(accentGreen)
					disconnectBtn.SetVisible(true)
				} else {
					statusLbl.SetText("WAITING FOR PAIRING")
					statusLbl.SetTextColor(walk.RGB(241, 196, 15))
					disconnectBtn.SetVisible(false)
				}
			})
		}
		if err := srv.Start(); err != nil {
			log.Printf("Server Start Error: %v", err)
			if mw != nil {
				mw.Synchronize(func() {
					outTE.SetText(outTE.Text() + "\nError: " + err.Error())
					statusLbl.SetText("ERROR")
					statusLbl.SetTextColor(walk.RGB(255, 0, 0))
				})
			}
		}
	}()

	// Define GUI Layout
	if _, err := (MainWindow{
		AssignTo:   &mw,
		Title:      serviceName,
		MinSize:    Size{Width: 450, Height: 500},
		Size:       Size{Width: 500, Height: 600},
		Layout:     VBox{},
		Background: SolidColorBrush{Color: bgLight},
		Font:       Font{Family: "Segoe UI", PointSize: 10},
		Children: []Widget{
			ScrollView{
				Layout: VBox{Margins: Margins{Left: 20, Top: 20, Right: 20, Bottom: 20}, Spacing: 15},
				Children: []Widget{
					// Header
					Composite{
						Layout: VBox{Spacing: 5},
						Children: []Widget{
							Label{Text: "APT DEFENDER SYSTEM [V2.0]", Font: Font{PointSize: 18, Bold: true}, TextColor: darkText},
							Label{Text: "Trusted Device Security Agent - PAIRING REQUIRED", TextColor: walk.RGB(231, 76, 60), Font: Font{PointSize: 9, Bold: true}},
						},
					},

					// PAIRING SECTION - AT TOP
					Composite{
						AssignTo: &pairingSection,
						Layout:   Grid{Columns: 2, Spacing: 10},
						Children: []Widget{
							Label{
								Text:       "CONNECTION REQUIRED",
								Font:       Font{Bold: true, PointSize: 11},
								TextColor:  walk.RGB(231, 76, 60), // Reddish for attention
								ColumnSpan: 2,
							},
							Label{Text: "Pi IP Address:"},
							LineEdit{AssignTo: &ipEdit, Text: "10.133.103.53"},
							Label{Text: "Pairing Code:"},
							LineEdit{AssignTo: &codeEdit, PasswordMode: true},
							PushButton{
								AssignTo:   &pairBtn,
								Text:       "Establish Trusted Link",
								ColumnSpan: 2,
								OnClicked: func() {
									piIP := ipEdit.Text()
									code := codeEdit.Text()
									if piIP == "" || code == "" {
										messageBox("Input Error", "Please enter both Pi IP and Pairing Code", 0x30)
										return
									}
									outTE.SetText(outTE.Text() + "\nInitiating pairing with " + piIP + "...")
									pairBtn.SetEnabled(false)
									go func() {
										err := performPairing(piIP, code, cfg, outTE, statusLbl, mw)
										mw.Synchronize(func() {
											pairBtn.SetEnabled(true)
											if err != nil {
												messageBox("Pairing Failed", err.Error(), 0x10)
											} else {
												messageBox("Success", "Device paired successfully!", 0x40)
											}
										})
									}()
								},
							},
						},
					},

					// Status Section
					Composite{
						Layout: HBox{Spacing: 10},
						Children: []Widget{
							Label{Text: "STATUS:", Font: Font{Bold: true}, TextColor: grayText},
							Label{AssignTo: &statusLbl, Text: "INITIALIZING...", Font: Font{PointSize: 11, Bold: true}},
						},
					},

					Label{
						Text:      fmt.Sprintf("Secure Endpoint: https://%s:%d", cfg.Host, cfg.Port),
						TextColor: accentGreen,
						Font:      Font{PointSize: 9, Bold: true},
					},

					Label{Text: "Activity Log", Font: Font{Bold: true}, TextColor: darkText},
					TextEdit{
						AssignTo:   &outTE,
						ReadOnly:   true,
						VScroll:    true,
						Background: SolidColorBrush{Color: white},
						Font:       Font{Family: "Consolas", PointSize: 9},
						MinSize:    Size{Width: 0, Height: 150},
					},

					PushButton{
						AssignTo: &disconnectBtn,
						Text:     "Disconnect from Pi Agent",
						Visible:  cfg.IsPaired,
						OnClicked: func() {
							if walk.MsgBox(mw, "Disconnect", "Are you sure you want to disconnect this device from the Pi Agent? You will need to re-pair to restore monitoring.", walk.MsgBoxIconWarning|walk.MsgBoxYesNo) == walk.DlgCmdNo {
								return
							}

							cfg.IsPaired = false
							cfg.PiAgentIP = ""
							cfg.Save(getConfigPath())

							statusLbl.SetText("DISCONNECTED")
							statusLbl.SetTextColor(walk.RGB(231, 76, 60))
							disconnectBtn.SetVisible(false)
							pairingSection.SetVisible(true)
							outTE.SetText(outTE.Text() + "\n❌ Device disconnected and configuration reset.")
						},
					},

					PushButton{
						Text:      "Minimize to Tray",
						OnClicked: func() { mw.Hide() },
					},
				},
			},
		},
	}.Run()); err != nil {
		log.Printf("GUI Error: %v", err)
		messageBox("Startup Error", "Failed to open GUI: "+err.Error(), 0x10)
	}
}

func performPairing(piIP, code string, cfg *config.Config, outTE *walk.TextEdit, statusLbl *walk.Label, mw *walk.MainWindow) error {
	hostname, _ := os.Hostname()
	localIP := getLocalIP()
	pairReq := map[string]interface{}{
		"pairing_token":     code,
		"device_hostname":   hostname,
		"device_ip":         localIP,
		"device_os":         "windows",
		"device_os_version": "10",
	}
	jsonBody, _ := json.Marshal(pairReq)
	url := fmt.Sprintf("http://%s:8443/api/v1/auth/pair", piIP)
	resp, err := http.Post(url, "application/json", bytes.NewBuffer(jsonBody))
	if err != nil {
		return fmt.Errorf("network error: %v", err)
	}
	defer resp.Body.Close()
	if resp.StatusCode != 200 {
		var errResp struct {
			Detail string `json:"detail"`
		}
		json.NewDecoder(resp.Body).Decode(&errResp)
		return fmt.Errorf("pi rejected pairing: %s", errResp.Detail)
	}

	mw.Synchronize(func() {
		outTE.SetText(outTE.Text() + "\n✅ PAIRING COMPLETE!")
		statusLbl.SetText("PAIRED & ACTIVE")
		statusLbl.SetTextColor(walk.RGB(46, 204, 113))
		disconnectBtn.SetVisible(true)
		cfg.PiAgentIP = piIP
		cfg.PiAgentPort = 8443
		cfg.IsPaired = true
		cfg.Save(getConfigPath())
	})
	return nil
}

func getAllLocalIPs() []string {
	var ips []string
	addrs, _ := net.InterfaceAddrs()
	for _, address := range addrs {
		if ipnet, ok := address.(*net.IPNet); ok && !ipnet.IP.IsLoopback() {
			if ipnet.IP.To4() != nil {
				ips = append(ips, ipnet.IP.String())
			}
		}
	}
	return ips
}

func getLocalIP() string {
	ips := getAllLocalIPs()
	if len(ips) == 0 {
		return "127.0.0.1"
	}

	// Prioritize common LAN ranges, avoid common VM ranges like 192.168.56.x
	for _, ip := range ips {
		// Prefer 10.x.x.x (matching the reported Pi IP range)
		if len(ip) > 3 && ip[:3] == "10." {
			return ip
		}
	}
	for _, ip := range ips {
		// Prefer 192.168.x.x but skip .56 (VirtualBox) and .232 (VMware common)
		if len(ip) > 8 && ip[:8] == "192.168." {
			if !bytes.Contains([]byte(ip), []byte(".56.")) && !bytes.Contains([]byte(ip), []byte(".232.")) {
				return ip
			}
		}
	}

	return ips[0]
}

func getConfigPath() string {
	if path := os.Getenv("HELPER_CONFIG"); path != "" {
		return path
	}
	if os.PathSeparator == '\\' {
		return "C:\\ProgramData\\APTDefender\\config.yaml"
	}
	return "/etc/apt-defender/config.yaml"
}
