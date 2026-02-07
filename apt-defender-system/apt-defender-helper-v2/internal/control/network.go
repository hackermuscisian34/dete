package control

import (
	"fmt"
	"log"
	"os/exec"
	"strings"
)

const (
	firewallRuleName = "APTDefender_Block_All"
)

// BlockAllNetwork blocks all network traffic using Windows Firewall
func BlockAllNetwork() error {
	log.Println("🚫 BLOCKING ALL NETWORK TRAFFIC...")

	// Create outbound blocking rule
	cmd := exec.Command("netsh", "advfirewall", "firewall", "add", "rule",
		"name="+firewallRuleName+"_Out",
		"dir=out",
		"action=block",
		"enable=yes",
	)
	if output, err := cmd.CombinedOutput(); err != nil {
		return fmt.Errorf("failed to block outbound traffic: %v, output: %s", err, output)
	}

	// Create inbound blocking rule
	cmd = exec.Command("netsh", "advfirewall", "firewall", "add", "rule",
		"name="+firewallRuleName+"_In",
		"dir=in",
		"action=block",
		"enable=yes",
	)
	if output, err := cmd.CombinedOutput(); err != nil {
		return fmt.Errorf("failed to block inbound traffic: %v, output: %s", err, output)
	}

	log.Println("✅ Network traffic blocked successfully")
	return nil
}

// UnblockAllNetwork removes the network blocking rules
func UnblockAllNetwork() error {
	log.Println("✅ RESTORING NETWORK ACCESS...")

	// Delete outbound blocking rule
	cmd := exec.Command("netsh", "advfirewall", "firewall", "delete", "rule",
		"name="+firewallRuleName+"_Out",
	)
	cmd.CombinedOutput() // Ignore errors if rule doesn't exist

	// Delete inbound blocking rule
	cmd = exec.Command("netsh", "advfirewall", "firewall", "delete", "rule",
		"name="+firewallRuleName+"_In",
	)
	cmd.CombinedOutput() // Ignore errors if rule doesn't exist

	log.Println("✅ Network access restored")
	return nil
}

// BlockApplication blocks a specific application from accessing the network
func BlockApplication(programPath string) error {
	log.Printf("🚫 BLOCKING APPLICATION: %s", programPath)

	ruleName := fmt.Sprintf("APTDefender_Block_App_%s", sanitizeRuleName(programPath))

	// Block outbound traffic for the application
	cmd := exec.Command("netsh", "advfirewall", "firewall", "add", "rule",
		"name="+ruleName,
		"dir=out",
		"action=block",
		"program="+programPath,
		"enable=yes",
	)
	if output, err := cmd.CombinedOutput(); err != nil {
		return fmt.Errorf("failed to block application: %v, output: %s", err, output)
	}

	log.Printf("✅ Application blocked: %s", programPath)
	return nil
}

// UnblockApplication removes network blocking for a specific application
func UnblockApplication(programPath string) error {
	log.Printf("✅ UNBLOCKING APPLICATION: %s", programPath)

	ruleName := fmt.Sprintf("APTDefender_Block_App_%s", sanitizeRuleName(programPath))

	cmd := exec.Command("netsh", "advfirewall", "firewall", "delete", "rule",
		"name="+ruleName,
	)
	if output, err := cmd.CombinedOutput(); err != nil {
		return fmt.Errorf("failed to unblock application: %v, output: %s", err, output)
	}

	log.Printf("✅ Application unblocked: %s", programPath)
	return nil
}

// GetNetworkStatus checks if network is currently blocked
func GetNetworkStatus() (bool, error) {
	cmd := exec.Command("netsh", "advfirewall", "firewall", "show", "rule",
		"name="+firewallRuleName+"_Out",
	)
	output, err := cmd.CombinedOutput()

	// If the rule exists, network is blocked
	if err != nil {
		// Rule doesn't exist, network is not blocked
		return false, nil
	}

	// Check if rule is enabled
	outputStr := string(output)
	if strings.Contains(outputStr, "Enabled") && strings.Contains(outputStr, "Yes") {
		return true, nil
	}

	return false, nil
}

// sanitizeRuleName removes invalid characters from firewall rule names
func sanitizeRuleName(s string) string {
	s = strings.ReplaceAll(s, "\\", "_")
	s = strings.ReplaceAll(s, "/", "_")
	s = strings.ReplaceAll(s, ":", "_")
	s = strings.ReplaceAll(s, " ", "_")
	if len(s) > 50 {
		s = s[:50]
	}
	return s
}
