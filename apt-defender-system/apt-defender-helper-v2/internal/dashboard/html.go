package dashboard

const HTML = `
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>APT Defender Helper - Dashboard</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            color: #fff;
            min-height: 100vh;
            padding: 20px;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
        }

        header {
            text-align: center;
            padding: 30px 0;
            border-bottom: 2px solid rgba(255,255,255,0.2);
            margin-bottom: 30px;
        }

        h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }

        .subtitle {
            font-size: 1.1em;
            opacity: 0.9;
        }

        .status {
            display: inline-block;
            padding: 8px 20px;
            background: #2ecc71;
            border-radius: 20px;
            margin-top: 15px;
            font-weight: bold;
        }

        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }

        .card {
            background: rgba(255,255,255,0.1);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 25px;
            border: 1px solid rgba(255,255,255,0.2);
            box-shadow: 0 8px 32px 0 rgba(0,0,0,0.37);
        }

        .card h2 {
            margin-bottom: 20px;
            font-size: 1.3em;
            color: #74ebd5;
        }

        .stat-row {
            display: flex;
            justify-content: space-between;
            margin: 12px 0;
            padding: 8px 0;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }

        .stat-label {
            font-weight: 500;
            opacity: 0.9;
        }

        .stat-value {
            font-weight: bold;
            color: #74ebd5;
        }

        .progress-bar {
            width: 100%;
            height: 25px;
            background: rgba(0,0,0,0.3);
            border-radius: 12px;
            overflow: hidden;
            margin-top: 10px;
        }

        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #74ebd5 0%, #ACB6E5 100%);
            transition: width 0.3s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            font-size: 0.9em;
        }

        .features {
            list-style: none;
        }

        .features li {
            padding: 10px 0;
            padding-left: 30px;
            position: relative;
        }

        .features li:before {
            content: "✓";
            position: absolute;
            left: 0;
            color: #2ecc71;
            font-weight: bold;
            font-size: 1.2em;
        }

        .actions {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
        }

        button {
            padding: 15px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border: none;
            border-radius: 8px;
            color: white;
            font-size: 1em;
            font-weight: bold;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
        }

        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(0,0,0,0.3);
        }

        button:active {
            transform: translateY(0);
        }

        .danger {
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        }

        .scan-status {
            background: rgba(0,0,0,0.2);
            padding: 15px;
            border-radius: 8px;
            margin-top: 15px;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }

        .scanning {
            animation: pulse 1.5s infinite;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🛡️ APT Defender Helper</h1>
            <p class="subtitle">Advanced PC Protection & Remote Control</p>
            <span class="status" id="connectionStatus">● CHECKING...</span>
        </header>

        <!-- IP Address Card (Prominent) -->
        <div class="card" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); margin-bottom: 30px; text-align: center;">
            <h2 style="color: white; margin-bottom: 15px;">📍 PC IP Addresses - Add to Mobile App</h2>
            <div id="ipAddresses" style="font-size: 1.5em; font-weight: bold; margin: 20px 0;"></div>
            <p style="opacity: 0.9; margin-bottom: 15px;">Use any of these IPs when adding this PC to your mobile app</p>
            <button onclick="copyIP()" style="background: rgba(255,255,255,0.2); border: 2px solid white;">
                📋 Copy First IP
            </button>
        </div>

        <div class="grid">
            <!-- System Stats -->
            <div class="card">
                <h2>💻 System Status</h2>
                <div class="stat-row">
                    <span class="stat-label">Hostname:</span>
                    <span class="stat-value" id="hostname">-</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">OS:</span>
                    <span class="stat-value" id="os">-</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">Uptime:</span>
                    <span class="stat-value" id="uptime">-</span>
                </div>
            </div>

            <!-- CPU Stats -->
            <div class="card">
                <h2>⚡ CPU Usage</h2>
                <div class="stat-row">
                    <span class="stat-label">Cores:</span>
                    <span class="stat-value" id="cpuCores">-</span>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill" id="cpuProgress" style="width: 0%">0%</div>
                </div>
            </div>

            <!-- Memory Stats -->
            <div class="card">
                <h2>🧠 Memory Usage</h2>
                <div class="stat-row">
                    <span class="stat-label">Total:</span>
                    <span class="stat-value" id="memTotal">-</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">Used:</span>
                    <span class="stat-value" id="memUsed">-</span>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill" id="memProgress" style="width: 0%">0%</div>
                </div>
            </div>

            <!-- Disk Stats -->
            <div class="card">
                <h2>💾 Disk Usage (C:)</h2>
                <div class="stat-row">
                    <span class="stat-label">Total:</span>
                    <span class="stat-value" id="diskTotal">-</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">Free:</span>
                    <span class="stat-value" id="diskFree">-</span>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill" id="diskProgress" style="width: 0%">0%</div>
                </div>
            </div>

            <!-- Features -->
            <div class="card">
                <h2>🔹 Available Features</h2>
                <ul class="features">
                    <li>File Scanning</li>
                    <li>Remote Shutdown/Restart</li>
                    <li>Workstation Lock</li>
                    <li>File Protection</li>
                    <li>Network Blocking</li>
                    <li>Real-time Telemetry</li>
                </ul>
            </div>

            <!-- Scanner Status -->
            <div class="card">
                <h2>🔍 Scanner Status</h2>
                <div class="stat-row">
                    <span class="stat-label">Status:</span>
                    <span class="stat-value" id="scanStatus">Idle</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">Files Scanned:</span>
                    <span class="stat-value" id="filesScanned">0</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">Threats Found:</span>
                    <span class="stat-value" id="threatsFound">0</span>
                </div>
                <div class="actions" style="margin-top: 15px;">
                    <button onclick="startScan()">Start Scan</button>
                    <button onclick="stopScan()">Stop Scan</button>
                </div>
            </div>
        </div>
    </div>

    <script>
        const API_BASE = window.location.origin + '/api/v1';
        let ipAddresses = [];

        // Fetch IP addresses on load
        fetchIPAddresses();

        async function fetchIPAddresses() {
            try {
                const response = await fetch(API_BASE + '/system/info');
                const data = await response.json();
                
                if (data.success && data.data.ip_addresses) {
                    ipAddresses = data.data.ip_addresses;
                    displayIPAddresses();
                    
                    // Update Pi Agent connection status
                    const statusEl = document.getElementById('connectionStatus');
                    if (data.data.registered_with_pi) {
                        statusEl.textContent = '● CONNECTED TO PI AGENT';
                        statusEl.style.background = '#2ecc71';
                        statusEl.title = 'Registered with Pi Agent at ' + data.data.pi_agent_ip;
                    } else {
                        statusEl.textContent = '● NOT REGISTERED';
                        statusEl.style.background = '#f39c12';
                        statusEl.title = 'This PC has not been added to a Pi Agent yet';
                    }
                }
            } catch (error) {
                console.error('Failed to fetch IP addresses:', error);
                document.getElementById('ipAddresses').innerHTML = '<span style="color: #ffcc00;">Unable to detect IPs</span>';
                document.getElementById('connectionStatus').textContent = '● DISCONNECTED';
                document.getElementById('connectionStatus').style.background = '#e74c3c';
            }
        }

        function displayIPAddresses() {
            const container = document.getElementById('ipAddresses');
            if (ipAddresses.length === 0) {
                container.textContent = 'No network interfaces found';
                return;
            }
            
            const ipHTML = ipAddresses.map(function(ip) {
                return '<div style="margin: 8px 0; padding: 10px; background: rgba(255,255,255,0.15); border-radius: 8px;">' + ip + '</div>';
            }).join('');
            container.innerHTML = ipHTML;
        }

        function copyIP() {
            if (ipAddresses.length === 0) {
                alert('No IP addresses available to copy');
                return;
            }
            
            const ip = ipAddresses[0]; // Copy first IP
            navigator.clipboard.writeText(ip).then(function() {
                alert('Copied: ' + ip + '\n\nNow open your mobile app and paste this in the "IP Address" field!');
            }).catch(function(err) {
                // Fallback for older browsers
                const textArea = document.createElement('textarea');
                textArea.value = ip;
                document.body.appendChild(textArea);
                textArea.select();
                document.execCommand('copy');
                document.body.removeChild(textArea);
                alert('Copied: ' + ip);
            });
        }

        // Update system stats every 2 seconds
        setInterval(updateStats, 2000);
        updateStats(); // Initial call

        // Update scan status every second
        setInterval(updateScanStatus, 1000);

        async function updateStats() {
            try {
                const response = await fetch(API_BASE + '/telemetry');
                const data = await response.json();
                
                if (data.success) {
                    const stats = data.data;
                    
                    // System info
                    document.getElementById('hostname').textContent = stats.system.hostname;
                    document.getElementById('os').textContent = stats.system.os + ' ' + stats.system.platform;
                    document.getElementById('uptime').textContent = formatUptime(stats.system.uptime_seconds);
                    
                    // CPU
                    document.getElementById('cpuCores').textContent = stats.cpu.cores;
                    updateProgress('cpuProgress', stats.cpu.usage_percent);
                    
                    // Memory
                    document.getElementById('memTotal').textContent = stats.memory.total_mb + ' MB';
                    document.getElementById('memUsed').textContent = stats.memory.used_mb + ' MB';
                    updateProgress('memProgress', stats.memory.usage_percent);
                    
                    // Disk
                    document.getElementById('diskTotal').textContent = stats.disk.total_gb + ' GB';
                    document.getElementById('diskFree').textContent = stats.disk.free_gb + ' GB';
                    updateProgress('diskProgress', stats.disk.usage_percent);
                    
                    document.getElementById('connectionStatus').textContent = '● CONNECTED';
                    document.getElementById('connectionStatus').style.background = '#2ecc71';
                }
            } catch (error) {
                console.error('Failed to update stats:', error);
                document.getElementById('connectionStatus').textContent = '● DISCONNECTED';
                document.getElementById('connectionStatus').style.background = '#e74c3c';
            }
        }

        async function updateScanStatus() {
            try {
                const response = await fetch(API_BASE + '/scan/status');
                const data = await response.json();
                
                if (data.success) {
                    const status = data.data;
                    document.getElementById('scanStatus').textContent = status.active ? 'Scanning...' : 'Idle';
                    document.getElementById('filesScanned').textContent = status.scanned_files;
                    document.getElementById('threatsFound').textContent = status.threats_found;
                }
            } catch (error) {
                // Silently fail if scan status not available
            }
        }

        async function startScan() {
            try {
                const response = await fetch(API_BASE + '/scan/start', { method: 'POST' });
                const data = await response.json();
                if (data.success) {
                    alert('Scan started successfully!');
                } else {
                    alert('Failed to start scan: ' + data.error);
                }
            } catch (error) {
                alert('Error starting scan: ' + error.message);
            }
        }

        async function stopScan() {
            try {
                const response = await fetch(API_BASE + '/scan/stop', { method: 'POST' });
                const data = await response.json();
                if (data.success) {
                    alert('Scan stopped successfully!');
                }
            } catch (error) {
                alert('Error stopping scan: ' + error.message);
            }
        }

        function updateProgress(id, percent) {
            const element = document.getElementById(id);
            const rounded = Math.round(percent);
            element.style.width = rounded + '%';
            element.textContent = rounded + '%';
        }

        function formatUptime(seconds) {
            const days = Math.floor(seconds / 86400);
            const hours = Math.floor((seconds % 86400) / 3600);
            const mins = Math.floor((seconds % 3600) / 60);
            return ` + "`" + `${days}d ${hours}h ${mins}m` + "`" + `;
        }
    </script>
</body>
</html>
`
