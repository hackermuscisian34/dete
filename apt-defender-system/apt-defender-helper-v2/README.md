# APT Defender Helper v2.0

A powerful Windows helper service for the APT Defender system, providing remote system control and security scanning capabilities.

## Features

### 🔍 File Scanning
- Multi-threaded file system scanning
- EICAR test file detection
- Hash-based malware detection
- Real-time progress reporting

### 💻 System Control
- Remote PC shutdown
- Remote PC restart
- Workstation lock

### 🔒 File Protection
- Lock files to read-only
- Prevent file deletion/modification
- Unlock protected files

### 🚫 Network Control
- Block all network traffic
- Restore network access
- Block specific applications
- Application-level firewall rules

## API Endpoints

All endpoints require Bearer token authentication.

### Scanner
- `POST /api/v1/scan/start` - Start file scan
- `GET /api/v1/scan/status` - Get scan progress
- `POST /api/v1/scan/stop` - Stop scan

### System Control
- `POST /api/v1/system/shutdown` - Shutdown PC
- `POST /api/v1/system/restart` - Restart PC
- `POST /api/v1/system/lock` - Lock workstation

### File Operations
- `POST /api/v1/files/lock` - Lock file (body: `{"path": "C:\\file.txt"}`)
- `POST /api/v1/files/unlock` - Unlock file

### Network Control
- `POST /api/v1/network/block` - Block all network
- `POST /api/v1/network/unblock` - Restore network
- `GET /api/v1/network/status` - Get network status
- `POST /api/v1/network/block-app` - Block application (body: `{"path": "C:\\app.exe"}`)

## Configuration

Config file location: `C:\ProgramData\APTDefender\helper-v2-config.yaml`

```yaml
host: "0.0.0.0"
port: 7890
auth_token: "your-secret-token"
enable_tls: false
log_level: "info"
scan_paths:
  - "C:\\Users\\YourName\\Downloads"
  - "C:\\Users\\YourName\\Documents"
  - "C:\\Users\\YourName\\Desktop"
```

## Building

```bash
# Install dependencies
go mod tidy

# Build executable
go build -ldflags="-H windowsgui" -o apt-defender-helper-v2.exe ./cmd/main.go
```

## Running

Double-click `apt-defender-helper-v2.exe` or run from command line:

```bash
apt-defender-helper-v2.exe
```

## Requirements

- Windows 10/11
- Administrator privileges (for shutdown, network blocking)
- Go 1.21+ (for building)

## Security Notes

⚠️ **IMPORTANT**: Change the default `auth_token` in production!

The helper service requires administrator privileges for:
- System shutdown/restart
- Modifying Windows Firewall rules
- File attribute changes

## License

Part of the APT Defender System
