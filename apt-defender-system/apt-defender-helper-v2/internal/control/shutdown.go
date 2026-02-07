package control

import (
	"fmt"
	"log"
	"os"
	"syscall"
	"unsafe"
)

var (
	user32   = syscall.NewLazyDLL("user32.dll")
	advapi32 = syscall.NewLazyDLL("advapi32.dll")
	kernel32 = syscall.NewLazyDLL("kernel32.dll")

	procExitWindowsEx         = user32.NewProc("ExitWindowsEx")
	procLockWorkStation       = user32.NewProc("LockWorkStation")
	procOpenProcessToken      = advapi32.NewProc("OpenProcessToken")
	procLookupPrivilegeValue  = advapi32.NewProc("LookupPrivilegeValueW")
	procAdjustTokenPrivileges = advapi32.NewProc("AdjustTokenPrivileges")
	procGetCurrentProcess     = kernel32.NewProc("GetCurrentProcess")
)

const (
	EWX_SHUTDOWN = 0x00000001
	EWX_REBOOT   = 0x00000002
	EWX_FORCE    = 0x00000004
	EWX_POWEROFF = 0x00000008

	TOKEN_ADJUST_PRIVILEGES = 0x0020
	TOKEN_QUERY             = 0x0008
	SE_PRIVILEGE_ENABLED    = 0x00000002
)

type LUID struct {
	LowPart  uint32
	HighPart int32
}

type LUID_AND_ATTRIBUTES struct {
	Luid       LUID
	Attributes uint32
}

type TOKEN_PRIVILEGES struct {
	PrivilegeCount uint32
	Privileges     [1]LUID_AND_ATTRIBUTES
}

// EnableShutdownPrivilege enables the necessary privilege to shutdown the system
func EnableShutdownPrivilege() error {
	var hToken syscall.Handle
	process, _, _ := procGetCurrentProcess.Call()

	ret, _, err := procOpenProcessToken.Call(
		process,
		TOKEN_ADJUST_PRIVILEGES|TOKEN_QUERY,
		uintptr(unsafe.Pointer(&hToken)),
	)
	if ret == 0 {
		return fmt.Errorf("OpenProcessToken failed: %v", err)
	}
	defer syscall.CloseHandle(hToken)

	var luid LUID
	shutdownName, _ := syscall.UTF16PtrFromString("SeShutdownPrivilege")
	ret, _, err = procLookupPrivilegeValue.Call(
		0,
		uintptr(unsafe.Pointer(shutdownName)),
		uintptr(unsafe.Pointer(&luid)),
	)
	if ret == 0 {
		return fmt.Errorf("LookupPrivilegeValue failed: %v", err)
	}

	tp := TOKEN_PRIVILEGES{
		PrivilegeCount: 1,
		Privileges: [1]LUID_AND_ATTRIBUTES{
			{
				Luid:       luid,
				Attributes: SE_PRIVILEGE_ENABLED,
			},
		},
	}

	ret, _, err = procAdjustTokenPrivileges.Call(
		uintptr(hToken),
		0,
		uintptr(unsafe.Pointer(&tp)),
		0,
		0,
		0,
	)
	if ret == 0 {
		return fmt.Errorf("AdjustTokenPrivileges failed: %v", err)
	}

	return nil
}

// ShutdownPC shuts down the computer
func ShutdownPC() error {
	log.Println("⚠️ SHUTDOWN REQUESTED - Shutting down PC...")

	if err := EnableShutdownPrivilege(); err != nil {
		return fmt.Errorf("failed to enable shutdown privilege: %w", err)
	}

	ret, _, err := procExitWindowsEx.Call(
		EWX_SHUTDOWN|EWX_POWEROFF|EWX_FORCE,
		0,
	)
	if ret == 0 {
		return fmt.Errorf("shutdown failed: %v", err)
	}

	return nil
}

// RestartPC restarts the computer
func RestartPC() error {
	log.Println("⚠️ RESTART REQUESTED - Restarting PC...")

	if err := EnableShutdownPrivilege(); err != nil {
		return fmt.Errorf("failed to enable shutdown privilege: %w", err)
	}

	ret, _, err := procExitWindowsEx.Call(
		EWX_REBOOT|EWX_FORCE,
		0,
	)
	if ret == 0 {
		return fmt.Errorf("restart failed: %v", err)
	}

	return nil
}

// LockWorkstation locks the user's workstation
func LockWorkstation() error {
	log.Println("🔒 LOCK REQUESTED - Locking workstation...")

	ret, _, err := procLockWorkStation.Call()
	if ret == 0 {
		return fmt.Errorf("lock workstation failed: %v", err)
	}

	return nil
}

// LockFile makes a file read-only to prevent modifications
func LockFile(path string) error {
	log.Printf("🔒 Locking file: %s", path)

	// Set file to read-only
	if err := os.Chmod(path, 0444); err != nil {
		return fmt.Errorf("failed to lock file: %w", err)
	}

	// Also set system and hidden attributes for extra protection
	pathPtr, _ := syscall.UTF16PtrFromString(path)
	attrs, err := syscall.GetFileAttributes(pathPtr)
	if err != nil {
		return fmt.Errorf("failed to get file attributes: %w", err)
	}

	// Add FILE_ATTRIBUTE_READONLY
	attrs |= syscall.FILE_ATTRIBUTE_READONLY
	if err := syscall.SetFileAttributes(pathPtr, attrs); err != nil {
		return fmt.Errorf("failed to set readonly attribute: %w", err)
	}

	return nil
}

// UnlockFile removes read-only protection from a file
func UnlockFile(path string) error {
	log.Printf("🔓 Unlocking file: %s", path)

	// Restore write permissions
	if err := os.Chmod(path, 0666); err != nil {
		return fmt.Errorf("failed to unlock file: %w", err)
	}

	pathPtr, _ := syscall.UTF16PtrFromString(path)
	attrs, err := syscall.GetFileAttributes(pathPtr)
	if err != nil {
		return fmt.Errorf("failed to get file attributes: %w", err)
	}

	// Remove FILE_ATTRIBUTE_READONLY
	attrs &^= syscall.FILE_ATTRIBUTE_READONLY
	if err := syscall.SetFileAttributes(pathPtr, attrs); err != nil {
		return fmt.Errorf("failed to remove readonly attribute: %w", err)
	}

	return nil
}
