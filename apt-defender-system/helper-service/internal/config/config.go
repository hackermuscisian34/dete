package config

import (
	"io/ioutil"
	"gopkg.in/yaml.v3"
)

// Config holds the service configuration
type Config struct {
	Host     string `yaml:"host"`
	Port     int    `yaml:"port"`
	CertFile string `yaml:"cert_file"`
	KeyFile  string `yaml:"key_file"`
	LogFile  string `yaml:"log_file"`
	
	// Security
	RateLimit       int  `yaml:"rate_limit"`        // Requests per minute
	EnableMTLS      bool `yaml:"enable_mtls"`
	PiCertFingerprint string `yaml:"pi_cert_fingerprint"`
}

// DefaultConfig returns default configuration
func DefaultConfig() *Config {
	return &Config{
		Host:     "127.0.0.1",
		Port:     7890,
		CertFile: "/etc/apt-defender/certs/helper.crt",
		KeyFile:  "/etc/apt-defender/certs/helper.key",
		LogFile:  "/var/log/apt-defender/helper.log",
		RateLimit: 100,
		EnableMTLS: true,
	}
}

// Load reads configuration from YAML file
func Load(path string) (*Config, error) {
	cfg := DefaultConfig()
	
	data, err := ioutil.ReadFile(path)
	if err != nil {
		// Use defaults if file doesn't exist
		return cfg, nil
	}
	
	err = yaml.Unmarshal(data, cfg)
	if err != nil {
		return nil, err
	}
	
	return cfg, nil
}
