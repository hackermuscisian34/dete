# APT Defender - Complete Setup Guide

This guide covers the end-to-end installation of the APT Defender system, including the Raspberry Pi Agent, Target PC Helper Service, Mobile App, and optional Supabase Cloud Sync.

---

## 🛠️ Step 1: Prerequisites

**Hardware:**
- **Raspberry Pi 4B** (detection hub)
- **Target PC** (Windows or Linux to protect)
- **Android/iOS Phone** (control interface)

**Software:**
- Python 3.11+ (on Pi)
- Go 1.21+ (on PC, for building helper)
- Node.js & Expo CLI (for mobile app)

---

## ☁️ Step 2: Supabase Cloud Setup (Optional)

If you want remote alerts on your phone when away from home:

1.  **Create Project:** Go to [database.new](https://database.new) and create a project.
2.  **Get Credentials:**
    - Go to **Project Settings** -> **API**.
    - Copy the **Project URL** and **anon / public Key**.
3.  **Run Schema:**
    - Go to the **SQL Editor** in Supabase.
    - Copy content from `database/supabase_schema.sql` in this repo.
    - Paste and run it to create tables (`devices`, `threats`, `alerts`).

---

## 🍓 Step 3: Raspberry Pi Agent Setup

**1. Prepare the Pi:**
```bash
sudo apt update
sudo apt install python3-pip python3-venv sqlite3 openssl
cd /opt
sudo git clone https://github.com/your-repo/apt-defender.git
cd apt-defender/pi-agent
```

**2. Install Environment:**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**3. Initialize Database (Local):**
```bash
# This creates the local SQLite DB required for offline operation
python -c "from database.db import init_database; import asyncio; asyncio.run(init_database())"
```

**4. Generate Certificates:**
```bash
sudo mkdir -p /opt/apt-defender/certs
sudo openssl req -x509 -newkey rsa:4096 -nodes \
  -out /opt/apt-defender/certs/server.crt \
  -keyout /opt/apt-defender/certs/server.key \
  -days 365 -subj "/CN=apt-defender-pi"
```

**5. Configure:**
Create `.env` file in `pi-agent/`:
```ini
HOST=0.0.0.0
PORT=8443
SSL_CERT=/opt/apt-defender/certs/server.crt
SSL_KEY=/opt/apt-defender/certs/server.key
JWT_SECRET=change_this_to_random_secret

# Supabase Settings (Update these!)
CLOUD_SYNC_ENABLED=True
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
```

**6. Start Service:**
```bash
python main.py
```

---

## 💻 Step 4: Target PC Helper Setup

**1. Build the Service:**
*On the target PC (Windows example):*
```powershell
cd helper-service
go build -o apt-defender-helper.exe cmd/main.go
```

**2. Setup Directories:**
Create `C:\ProgramData\APTDefender\` and `C:\ProgramData\APTDefender\certs\`.

**3. Generate Certificates:**
Run the tool included in the repo:
```powershell
go run tools/gen_certs.go
```

**4. Configure:**
Create `C:\ProgramData\APTDefender\config.yaml`:
```yaml
host: 127.0.0.1
port: 7890
cert_file: C:\ProgramData\APTDefender\certs\helper.crt
key_file: C:\ProgramData\APTDefender\certs\helper.key
enable_mtls: true
```

**5. Run Service:**
Run `apt-defender-helper.exe` as Administrator.

---

## 📱 Step 5: Mobile App Setup

**1. Install Dependencies:**
```bash
cd mobile-app
npm install
```

**2. Configure API:**
Edit `src/api/piClient.js`:
```javascript
const API_BASE_URL = 'https://<YOUR-PI-IP-ADDRESS>:8443/api/v1';
```

**3. Run App:**
```bash
npx expo start
```
Scan the QR code with your phone (Expo Go app).

---

## ✅ Step 6: Verify Everything

1.  **Check Pi:** `curl -k https://localhost:8443/health` -> `{"status": "healthy"}`
2.  **Check Helper:** `curl -k https://localhost:7890/v1/health` -> `{"status": "healthy"}`
3.  **App Login:** Open app, it should connect to Pi.
4.  **Pair Device:**
    - On Pi: `curl -k -X POST .../auth/generate-pairing-code`
    - Enter code in App.
    - Device appears in list.
5.  **Test Sync:**
    - Trigger a scan or simulated threat.
    - Check your Supabase dashboard `threats` table to see the data appear.
