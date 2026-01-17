# apt-defender-system

A portable detection and response system for identifying APTs (Advanced Persistent Threats) on compromised devices using a trusted Raspberry Pi agent.

## 🚀 Quick Start (Complete System Setup)

This guide will help you set up the entire system (Pi Agent, Helper Service, Mobile App).

### 📋 Prerequisites
*   **Hardware:** Raspberry Pi 4B, Target PC (Windows/Linux), Mobile Phone.
*   **Network:** All devices must be on the same WiFi/LAN.

### 1️⃣ Raspberry Pi Agent (The Brains)
1.  **Install Dependencies:**
    ```bash
    cd pi-agent
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    pip install -r requirements.txt
    ```
2.  **Initialize Database:**
    ```bash
    python -c "from database.db import init_database; import asyncio; asyncio.run(init_database())"
    ```
3.  **Generate Certificates:**
    ```bash
    # Create directory
    sudo mkdir -p /opt/apt-defender/certs
    
    # Generate CA and Server Certs (simplified for dev)
    openssl req -x509 -newkey rsa:4096 -nodes -out /opt/apt-defender/certs/server.crt -keyout /opt/apt-defender/certs/server.key -days 365 -subj "/CN=your-pi-hostname"
    ```
4.  **Configure:** Copy `config/settings.example.py` to `config/settings.py` (if needed) or set env vars.
5.  **Run:**
    ```bash
    python main.py
    ```

### 2️⃣ Target PC Helper Service (The Muscle)
1.  **Build Binary:**
    ```powershell
    cd helper-service
    go mod tidy
    go build -o bin/apt-defender-helper.exe cmd/main.go
    ```
2.  **Generate Certificates (Windows):**
    ```powershell
    # Creates C:\ProgramData\APTDefender\certs
    go run tools/gen_certs.go 
    ```
3.  **Run Service:**
    Run as Administrator:
    ```powershell
    .\bin\apt-defender-helper.exe
    ```

### 3️⃣ Mobile App (The Controls)
1.  **Install:**
    ```bash
    cd mobile-app
    npm install
    ```
2.  **Run:**
    ```bash
    npx expo start
    ```
3.  **Connect:** Scan the QR code with your phone (Expo Go app).

---

## 🏗️ Architecture

*   **Raspberry Pi Agent (Python/FastAPI):** Central hub. Scans files, detects threats, hosts the database.
*   **Helper Service (Go):** Runs on the target PC. Executes privileged commands (kill process, quarantine file).
*   **Mobile App (React Native):** User interface for alerts and manual actions.

## 📚 Documentation
*   [User Guide](docs/USER_GUIDE.md) - How to use the system day-to-day.
*   [Technical Docs](docs/TECHNICAL_DOCS.md) - Deep dive into architecture and code.
*   [Setup Guide](docs/SETUP.md) - Detailed step-by-step installation.

## 🔐 Security
*   **mTLS:** All communication between Pi and PC is mutually authenticated.
*   **Offline First:** Works without internet. Cloud sync is optional.
*   **Least Privilege:** Helper service limits what commands can be run.

## 🧪 Testing
Run the simulated attack test to verify the system:
1.  Connect Pi and PC.
2.  Run `tests/simulation/attack_sim.ps1` on PC (simulates a beaconing malware).
3.  Check Mobile App for alerts.

## 📄 License
MIT License
