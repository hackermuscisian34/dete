package config

import (
	"fmt"
	"os"

	"gopkg.in/yaml.v3"
)

type Config struct {
	Host             string   `yaml:"host"`
	Port             int      `yaml:"port"`
	AuthToken        string   `yaml:"auth_token"`
	EnableTLS        bool     `yaml:"enable_tls"`
	CertFile         string   `yaml:"cert_file"`
	KeyFile          string   `yaml:"key_file"`
	LogLevel         string   `yaml:"log_level"`
	ScanPaths        []string `yaml:"scan_paths"`
	PiAgentIP        string   `yaml:"pi_agent_ip"`        // IP of the Pi Agent this PC is registered with
	RegisteredWithPi bool     `yaml:"registered_with_pi"` // Whether this PC has been registered
}

func Load(path string) (*Config, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		// Return default config if file doesn't exist
		if os.IsNotExist(err) {
			return DefaultConfig(), nil
		}
		return nil, fmt.Errorf("failed to read config: %w", err)
	}

	var cfg Config
	if err := yaml.Unmarshal(data, &cfg); err != nil {
		return nil, fmt.Errorf("failed to parse config: %w", err)
	}

	return &cfg, nil
}

func (c *Config) Save(path string) error {
	data, err := yaml.Marshal(c)
	if err != nil {
		return fmt.Errorf("failed to marshal config: %w", err)
	}

	if err := os.WriteFile(path, data, 0600); err != nil {
		return fmt.Errorf("failed to write config: %w", err)
	}

	return nil
}

func DefaultConfig() *Config {
	homeDir, _ := os.UserHomeDir()
	return &Config{
		Host:             "0.0.0.0",
		Port:             7890,
		AuthToken:        "change-me-in-production",
		EnableTLS:        false, // Start simple, enable later
		LogLevel:         "info",
		PiAgentIP:        "",    // Not registered yet
		RegisteredWithPi: false, // Not registered yet
		ScanPaths: []string{
			homeDir + "\\Downloads",
			homeDir + "\\Documents",
			homeDir + "\\Desktop",
		},
	}
}

func GetConfigPath() string {
	if path := os.Getenv("HELPER_CONFIG"); path != "" {
		return path
	}
	return "C:\\ProgramData\\APTDefender\\helper-v2-config.yaml"
}
