package telemetry

import (
	"fmt"
	"os"
	"runtime"
	"syscall"
	"time"
	"unsafe"
)

type SystemStats struct {
	Timestamp time.Time `json:"timestamp"`
	CPU       CPUStats  `json:"cpu"`
	Memory    MemStats  `json:"memory"`
	Disk      DiskStats `json:"disk"`
	Network   NetStats  `json:"network"`
	System    SysInfo   `json:"system"`
}

type CPUStats struct {
	UsagePercent float64 `json:"usage_percent"`
	Cores        int     `json:"cores"`
}

type MemStats struct {
	TotalMB      uint64  `json:"total_mb"`
	UsedMB       uint64  `json:"used_mb"`
	AvailableMB  uint64  `json:"available_mb"`
	UsagePercent float64 `json:"usage_percent"`
}

type DiskStats struct {
	TotalGB      uint64  `json:"total_gb"`
	UsedGB       uint64  `json:"used_gb"`
	FreeGB       uint64  `json:"free_gb"`
	UsagePercent float64 `json:"usage_percent"`
}

type NetStats struct {
	BytesSent   uint64 `json:"bytes_sent"`
	BytesRecv   uint64 `json:"bytes_recv"`
	PacketsSent uint64 `json:"packets_sent"`
	PacketsRecv uint64 `json:"packets_recv"`
}

type SysInfo struct {
	Hostname string `json:"hostname"`
	OS       string `json:"os"`
	Platform string `json:"platform"`
	Uptime   uint64 `json:"uptime_seconds"`
}

var (
	kernel32           = syscall.NewLazyDLL("kernel32.dll")
	procGetSystemTimes = kernel32.NewProc("GetSystemTimes")
)

// GetSystemStats collects comprehensive system statistics
func GetSystemStats() (*SystemStats, error) {
	stats := &SystemStats{
		Timestamp: time.Now(),
	}

	// CPU Info
	stats.CPU = CPUStats{
		Cores:        runtime.NumCPU(),
		UsagePercent: getCPUUsage(),
	}

	// Memory Info
	memStats, err := getMemoryStats()
	if err == nil {
		stats.Memory = *memStats
	}

	// Disk Info
	diskStats, err := getDiskStats("C:\\")
	if err == nil {
		stats.Disk = *diskStats
	}

	// System Info
	hostname, _ := os.Hostname()
	stats.System = SysInfo{
		Hostname: hostname,
		OS:       "Windows",
		Platform: runtime.GOARCH,
		Uptime:   getUptime(),
	}

	return stats, nil
}

func getCPUUsage() float64 {
	// Simple CPU usage estimation
	var idleTime, kernelTime, userTime syscall.Filetime

	ret, _, _ := procGetSystemTimes.Call(
		uintptr(unsafe.Pointer(&idleTime)),
		uintptr(unsafe.Pointer(&kernelTime)),
		uintptr(unsafe.Pointer(&userTime)),
	)

	if ret == 0 {
		return 0.0
	}

	idle := float64(idleTime.Nanoseconds())
	system := float64(kernelTime.Nanoseconds() + userTime.Nanoseconds())

	if system == 0 {
		return 0.0
	}

	usage := ((system - idle) / system) * 100
	if usage < 0 {
		usage = 0
	}
	if usage > 100 {
		usage = 100
	}

	return usage
}

func getMemoryStats() (*MemStats, error) {
	type memStatusEx struct {
		Length               uint32
		MemoryLoad           uint32
		TotalPhys            uint64
		AvailPhys            uint64
		TotalPageFile        uint64
		AvailPageFile        uint64
		TotalVirtual         uint64
		AvailVirtual         uint64
		AvailExtendedVirtual uint64
	}

	var memStatus memStatusEx
	memStatus.Length = uint32(unsafe.Sizeof(memStatus))

	kernel32 := syscall.NewLazyDLL("kernel32.dll")
	procGlobalMemoryStatusEx := kernel32.NewProc("GlobalMemoryStatusEx")

	ret, _, _ := procGlobalMemoryStatusEx.Call(uintptr(unsafe.Pointer(&memStatus)))
	if ret == 0 {
		return nil, fmt.Errorf("GlobalMemoryStatusEx failed")
	}

	totalMB := memStatus.TotalPhys / 1024 / 1024
	availMB := memStatus.AvailPhys / 1024 / 1024
	usedMB := totalMB - availMB

	return &MemStats{
		TotalMB:      totalMB,
		UsedMB:       usedMB,
		AvailableMB:  availMB,
		UsagePercent: float64(memStatus.MemoryLoad),
	}, nil
}

func getDiskStats(path string) (*DiskStats, error) {
	var freeBytesAvailable, totalBytes, totalFreeBytes uint64

	pathPtr, err := syscall.UTF16PtrFromString(path)
	if err != nil {
		return nil, err
	}

	kernel32 := syscall.NewLazyDLL("kernel32.dll")
	procGetDiskFreeSpaceEx := kernel32.NewProc("GetDiskFreeSpaceExW")

	ret, _, _ := procGetDiskFreeSpaceEx.Call(
		uintptr(unsafe.Pointer(pathPtr)),
		uintptr(unsafe.Pointer(&freeBytesAvailable)),
		uintptr(unsafe.Pointer(&totalBytes)),
		uintptr(unsafe.Pointer(&totalFreeBytes)),
	)
	if ret == 0 {
		return nil, fmt.Errorf("GetDiskFreeSpaceEx failed")
	}

	totalGB := totalBytes / 1024 / 1024 / 1024
	freeGB := totalFreeBytes / 1024 / 1024 / 1024
	usedGB := totalGB - freeGB

	usage := 0.0
	if totalGB > 0 {
		usage = (float64(usedGB) / float64(totalGB)) * 100
	}

	return &DiskStats{
		TotalGB:      totalGB,
		UsedGB:       usedGB,
		FreeGB:       freeGB,
		UsagePercent: usage,
	}, nil
}

func getUptime() uint64 {
	kernel32 := syscall.NewLazyDLL("kernel32.dll")
	procGetTickCount64 := kernel32.NewProc("GetTickCount64")
	ret, _, _ := procGetTickCount64.Call()
	return uint64(ret) / 1000 // Convert ms to seconds
}

// MonitorContinuously returns a channel that emits stats every interval
func MonitorContinuously(interval time.Duration) <-chan *SystemStats {
	ch := make(chan *SystemStats)

	go func() {
		ticker := time.NewTicker(interval)
		defer ticker.Stop()

		for range ticker.C {
			if stats, err := GetSystemStats(); err == nil {
				ch <- stats
			}
		}
	}()

	return ch
}
