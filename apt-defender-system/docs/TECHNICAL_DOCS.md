# APT Defender - Technical Documentation

**For System Administrators and Security Teams**

## System Architecture

```
┌──────────────────────┐
│   Mobile App         │
│   (User Interface)   │
└──────────┬───────────┘
           │ HTTPS/JWT Auth
           ▼
┌──────────────────────┐
│  Raspberry Pi 4B     │
│  Detection Hub       │
│  - FastAPI           │
│  - SQLite            │
│  - YARA Engine       │
│  - Network IDS       │
└──────────┬───────────┘
           │ mTLS/Whitelisted API
           ▼
┌──────────────────────┐
│  Target PC           │
│  Helper Service      │
│  - Go Binary         │
│  - Localhost Only    │
└──────────────────────┘
```

## Component Deep Dive

### Raspberry Pi Agent

**Technology Stack:**
- Python 3.11+
- FastAPI (REST API)
- SQLAlchemy (ORM)
- YARA (pattern matching)
- psutil (system monitoring)

**Modules:**

| Module | Purpose | Files |
| --- | --- | --- |
| API Server | REST endpoints for mobile app | `api/server.py`, `api/routes/*` |
| Authentication | JWT token management | `api/auth.py` |
| Database | SQLite persistence | `database/db.py` |
| Hash Scanner | SHA256 + VirusTotal | `detection/hash_scanner.py` |
| YARA Engine | Rule-based detection | `detection/yara_engine.py` |
| Beaconing Detector | Statistical C2 detection | `detection/beaconing.py` |
| Helper Client | PC connector | `connector/helper_client.py` |

**Installation:**

```bash
# On Raspberry Pi
cd /opt
sudo git clone <repo> apt-defender
cd apt-defender/pi-agent

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Initialize database
python -c "from database.db import init_database; import asyncio; asyncio.run(init_database())"

# Generate SSL certificates
sudo apt-get install openssl
openssl req -x509 -newkey rsa:4096 -nodes \
  -out /opt/apt-defender/certs/server.crt \
  -keyout /opt/apt-defender/certs/server.key \
  -days 365

# Create systemd service
sudo cp systemd/apt-defender.service /etc/systemd/system/
sudo systemctl enable apt-defender
sudo systemctl start apt-defender
```

**Configuration:**

Edit `/opt/apt-defender/.env`:

```ini
# Server
HOST=0.0.0.0
PORT=8443
SSL_CERT=/opt/apt-defender/certs/server.crt
SSL_KEY=/opt/apt-defender/certs/server.key

# JWT
JWT_SECRET=<generate-random-secret>
JWT_EXPIRATION_HOURS=24

# Detection
SCAN_INTERVAL_HOURS=24
AUTO_QUARANTINE=true
ALERT_THRESHOLD_SEVERITY=7

# Optional: VirusTotal API
VT_API_KEY=<your-key>

# Optional: Cloud Sync
CLOUD_SYNC_ENABLED=false
SUPABASE_URL=
SUPABASE_KEY=
```

### Helper Service

**Technology Stack:**
- Go 1.21+
- Gorilla Mux (HTTP routing)
- gopsutil (system info)

**API Endpoints:**

| Endpoint | Method | Purpose | Requires Root |
|----------|--------|---------|---------------|
| `/v1/health` | GET | Service status | No |
| `/v1/processes` | GET | Running processes | No |
| `/v1/files/hash` | GET | Calculate file hash | No |
| `/v1/process/kill` | POST | Terminate process | Yes |
| `/v1/file/quarantine` | POST | Move to quarantine | Yes |
| `/v1/network/disable` | POST | Block network | Yes |
| `/v1/system/lock` | POST | Lock screen | No |
| `/v1/system/shutdown` | POST | Shutdown system | Yes |
| `/v1/persistence` | GET | Check autoruns | No |
| `/v1/network/connections` | GET | Active connections | No |

**Installation (Windows):**

```powershell
# Run as Administrator
msiexec /i APTDefender-Helper.msi /quiet

# Service starts automatically
# Config: C:\ProgramData\APTDefender\config.yaml
```

**Installation (Linux):**

```bash
# Debian/Ubuntu
sudo dpkg -i apt-defender-helper_1.0.0_amd64.deb

# RHEL/CentOS
sudo rpm -i apt-defender-helper-1.0.0.x86_64.rpm

# Start service
sudo systemctl start apt-defender-helper
sudo systemctl enable apt-defender-helper
```

**Configuration:**

Edit `config.yaml`:

```yaml
host: 127.0.0.1
port: 7890
cert_file: /etc/apt-defender/certs/helper.crt
key_file: /etc/apt-defender/certs/helper.key
log_file: /var/log/apt-defender/helper.log
rate_limit: 100  # requests per minute
enable_mtls: true
pi_cert_fingerprint: "SHA256:..."
```

### Mobile Application

**Technology Stack:**
- React Native 0.73
- Expo SDK 50
- React Navigation 6
- Axios (HTTP client)

**Screens:**

| Screen | Route | Purpose |
|--------|-------|---------|
| Login | `/login` | Authentication |
| Devices | `/devices` | Device list |
| DeviceDetail | `/devices/:id` | Actions & status |
| Alerts | `/alerts` | Notification feed |
| AlertDetail | `/alerts/:id` | Threat details |
| Settings | `/settings` | Configuration |

**Building:**

```bash
cd mobile-app

# Install dependencies
npm install

# Run on device
npm run android  # Android
npm run ios      # iOS

# Build release
eas build --platform android
eas build --platform ios
```

## Database Schema

See `/database/schema.sql` for full schema.

**Key Tables:**

- `devices` — Paired computers
- `threats` — Detected threats
- `scans` — Scan history
- `network_events` — Network traffic
- `actions` — Response actions
- `forensic_timeline` — Event log
- `yara_rules` — Detection rules

**Sample Queries:**

```sql
-- Active threats by device
SELECT d.hostname, COUNT(t.id) as threats
FROM devices d
LEFT JOIN threats t ON d.id = t.device_id AND t.dismissed = 0
GROUP BY d.id;

-- Recent high-severity threats
SELECT * FROM active_threats
WHERE severity >= 8
ORDER BY detected_at DESC
LIMIT 10;

-- Device scan history
SELECT hostname, started_at, files_checked, threats_found
FROM scans s
JOIN devices d ON s.device_id = d.id
WHERE d.id = 1
ORDER BY started_at DESC;
```

## Security Implementation

### Authentication Flow

1. **Initial Pairing:**
   - Pi generates pairing token (32 bytes, 5-min expiry)
   - User enters token in mobile app
   - Pi validates token, issues JWT (24hr expiry)
   - Token stored in device secure storage (Keychain/Keystore)

2. **Ongoing Requests:**
   - Mobile app sends: `Authorization: Bearer <JWT>`
   - Pi validates signature and expiry
   - Pi checks device_id in token matches request

3. **Helper Service:**
   - mTLS with certificate pinning
   - Helper only accepts connections from paired Pi
   - Certificates rotated monthly

### Network Security

**TLS Everywhere:**
- Mobile ↔ Pi: HTTPS with TLS 1.3
- Pi ↔ Helper: HTTPS with mTLS
- Certificate pinning on all connections

**Firewall Rules:**

```bash
# Pi Agent (should be on LAN only)
sudo ufw allow from 192.168.1.0/24 to any port 8443

# Helper Service (localhost only)
# No firewall rules needed — binds to 127.0.0.1
```

### Threat Model

**Assumptions:**
1. Raspberry Pi is trusted (physical security required)
2. Target PC may be compromised
3. Network may have passive eavesdroppers
4. Mobile device may be stolen

**Mitigations:**

| Threat | Mitigation |
|--------|------------|
| Malware kills Helper service | Pi detects missing heartbeat, alerts user |
| Malware modifies Helper binary | Code signing + integrity checks |
| Network MITM attack | Certificate pinning, TLS |
| Stolen mobile device | Biometric auth, auto-logout |
| Compromised Pi | Disk encryption (LUKS), secure boot |
| Helper exploitation | Whitelisted API, no arbitrary commands |

## Deployment

### Production Checklist

**Raspberry Pi:**
- [ ] Change default passwords
- [ ] Enable disk encryption
- [ ] Set strong JWT secret
- [ ] Configure firewall (UFW)
- [ ] Enable automatic updates
- [ ] Set up log rotation
- [ ] Configure backup script

**Helper Service:**
- [ ] Verify code signature
- [ ] Check certificate expiry
- [ ] Test all API endpoints
- [ ] Verify service auto-starts
- [ ] Check log permissions

**Mobile App:**
- [ ] Update API base URL
- [ ] Configure push notifications
- [ ] Test on real devices
- [ ] Submit to app stores

### Monitoring

**Health Checks:**

```bash
# Pi Agent
curl -k https://localhost:8443/health

# Helper Service
curl -k https://localhost:7890/v1/health
```

**Logs:**

```bash
# Pi Agent
tail -f /var/log/apt-defender/agent.log

# Helper Service (Linux)
journalctl -u apt-defender-helper -f

# Helper Service (Windows)
Get-EventLog -LogName Application -Source "APT Defender"
```

## Performance Tuning

### Raspberry Pi Optimization

```ini
# /boot/config.txt
# Increase GPU memory
gpu_mem=256

# Overclock (Pi 4 only)
over_voltage=6
arm_freq=2000
```

### Database Optimization

```sql
-- Add indexes for common queries
CREATE INDEX idx_threats_device_severity ON threats(device_id, severity DESC);
CREATE INDEX idx_forensic_device_time ON forensic_timeline(device_id, timestamp DESC);

-- Vacuum regularly
VACUUM;
ANALYZE;
```

### Scan Performance

**Limits:**
- 500,000 files per scan (adjust in settings)
- 10 concurrent YARA scans
- Network IDS processes 1000 events/sec

## Troubleshooting

### Pi Agent Won't Start

```bash
# Check logs
journalctl -u apt-defender -n 50

# Common issues:
# 1. Database locked
sudo systemctl stop apt-defender
sudo rm -f /opt/apt-defender/data/defender.db-lock
sudo systemctl start apt-defender

# 2. Port already in use
sudo lsof -i :8443
sudo kill <PID>

# 3. Certificate issue
openssl verify /opt/apt-defender/certs/server.crt
```

### Helper Service Can't Connect

**Windows:**
```powershell
# Check service status
Get-Service "APT Defender Helper"

# Restart service
Restart-Service "APT Defender Helper"

# Check firewall
Get-NetFirewallRule -DisplayName "*APT*"
```

**Linux:**
```bash
# Service status
systemctl status apt-defender-helper

# Check logs
journalctl -u apt-defender-helper -n 100

# Test endpoint
curl -k https://localhost:7890/v1/health
```

### Mobile App Connection Issues

1. Check Pi is online: `ping <pi-ip>`
2. Verify port is open: `nmap -p 8443 <pi-ip>`
3. Check JWT token hasn't expired
4. Clear app cache and re-login

## API Reference

See `/docs/API.md` for full API documentation.

**Quick Examples:**

```bash
# Get authentication token
curl -X POST https://pi-ip:8443/api/v1/auth/pair \
  -H "Content-Type: application/json" \
  -d '{"pairing_token":"abc123","device_hostname":"laptop"}'

# List devices
curl -H "Authorization: Bearer <token>" \
  https://pi-ip:8443/api/v1/devices

# Trigger scan
curl -X POST \
  -H "Authorization: Bearer <token>" \
  https://pi-ip:8443/api/v1/devices/1/scan
```

## Contributing

See `CONTRIBUTING.md` for development guidelines.

**Development Setup:**

```bash
# Pi Agent
cd pi-agent
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
pytest tests/

# Helper Service
cd helper-service
go mod download
go test ./...

# Mobile App
cd mobile-app
npm install
npm test
```

---

**Support:** support@apt-defender.local  
**Documentation:** https://docs.apt-defender.local
