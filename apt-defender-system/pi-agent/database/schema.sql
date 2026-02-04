-- APT Defender SQLite Database Schema
-- Version: 1.0
-- Target: Raspberry Pi Detection Agent

-- ============================================
-- DEVICES TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS devices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hostname TEXT NOT NULL,
    os TEXT NOT NULL CHECK(os IN ('windows', 'linux', 'macos')),
    os_version TEXT,
    paired_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'online' CHECK(status IN ('online', 'offline', 'threat', 'isolated')),
    ip_address TEXT,
    helper_version TEXT,
    pairing_token TEXT UNIQUE,
    cert_fingerprint TEXT,
    UNIQUE(hostname, os)
);

CREATE INDEX IF NOT EXISTS idx_devices_status ON devices(status);
CREATE INDEX IF NOT EXISTS idx_devices_last_seen ON devices(last_seen);

-- ============================================
-- THREATS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS threats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id INTEGER NOT NULL,
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    severity INTEGER NOT NULL CHECK(severity BETWEEN 1 AND 10),
    type TEXT NOT NULL CHECK(type IN ('malware', 'apt', 'anomaly', 'persistence', 'network', 'beaconing')),
    indicator TEXT NOT NULL, -- file path, process name, or IP:port
    hash_value TEXT, -- SHA256 if applicable
    explanation TEXT NOT NULL, -- Plain English description
    recommended_action TEXT CHECK(recommended_action IN ('quarantine', 'kill', 'investigate', 'block', 'isolate')),
    action_taken TEXT,
    dismissed BOOLEAN DEFAULT 0,
    dismissed_at TIMESTAMP,
    dismissed_reason TEXT,
    evidence JSON, -- Additional detection data
    FOREIGN KEY (device_id) REFERENCES devices(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_threats_device ON threats(device_id);
CREATE INDEX IF NOT EXISTS idx_threats_severity ON threats(severity DESC);
CREATE INDEX IF NOT EXISTS idx_threats_detected_at ON threats(detected_at DESC);
CREATE INDEX IF NOT EXISTS idx_threats_dismissed ON threats(dismissed);

-- ============================================
-- SCANS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS scans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id INTEGER NOT NULL,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    status TEXT DEFAULT 'running' CHECK(status IN ('running', 'completed', 'failed', 'cancelled')),
    total_files INTEGER DEFAULT 0,
    files_checked INTEGER DEFAULT 0,
    threats_found INTEGER DEFAULT 0,
    scan_type TEXT DEFAULT 'full' CHECK(scan_type IN ('full', 'quick', 'custom')),
    error_message TEXT,
    FOREIGN KEY (device_id) REFERENCES devices(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_scans_device ON scans(device_id);
CREATE INDEX IF NOT EXISTS idx_scans_started_at ON scans(started_at DESC);

-- ============================================
-- NETWORK EVENTS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS network_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id INTEGER NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    src_ip TEXT NOT NULL,
    dst_ip TEXT NOT NULL,
    src_port INTEGER,
    dst_port INTEGER,
    protocol TEXT CHECK(protocol IN ('TCP', 'UDP', 'ICMP', 'OTHER')),
    alert_type TEXT, -- beaconing, c2, exfiltration, etc.
    process_name TEXT,
    process_pid INTEGER,
    bytes_sent INTEGER DEFAULT 0,
    bytes_received INTEGER DEFAULT 0,
    FOREIGN KEY (device_id) REFERENCES devices(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_network_device ON network_events(device_id);
CREATE INDEX IF NOT EXISTS idx_network_timestamp ON network_events(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_network_dst_ip ON network_events(dst_ip);

-- ============================================
-- ACTIONS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS actions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id INTEGER NOT NULL,
    threat_id INTEGER, -- NULL if manual action
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    action_type TEXT NOT NULL CHECK(action_type IN ('kill', 'quarantine', 'lock', 'shutdown', 'isolate', 'restore')),
    target TEXT NOT NULL, -- PID, file path, etc.
    result TEXT DEFAULT 'pending' CHECK(result IN ('pending', 'success', 'failed')),
    error_message TEXT,
    initiated_by TEXT NOT NULL, -- 'user_mobile', 'auto_response', 'admin'
    reversible BOOLEAN DEFAULT 1,
    reversed_at TIMESTAMP,
    FOREIGN KEY (device_id) REFERENCES devices(id) ON DELETE CASCADE,
    FOREIGN KEY (threat_id) REFERENCES threats(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_actions_device ON actions(device_id);
CREATE INDEX IF NOT EXISTS idx_actions_timestamp ON actions(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_actions_threat ON actions(threat_id);

-- ============================================
-- FORENSIC TIMELINE TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS forensic_timeline (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id INTEGER NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    event_type TEXT NOT NULL, -- process_created, file_modified, network_connection, etc.
    details TEXT NOT NULL, -- JSON or plain text
    source TEXT NOT NULL CHECK(source IN ('helper', 'network_ids', 'file_monitor', 'process_monitor')),
    severity INTEGER DEFAULT 0 CHECK(severity BETWEEN 0 AND 10),
    FOREIGN KEY (device_id) REFERENCES devices(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_forensic_device ON forensic_timeline(device_id);
CREATE INDEX IF NOT EXISTS idx_forensic_timestamp ON forensic_timeline(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_forensic_event_type ON forensic_timeline(event_type);

-- ============================================
-- YARA RULES TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS yara_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    rule_content TEXT NOT NULL,
    enabled BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    description TEXT,
    author TEXT,
    tags TEXT -- Comma-separated
);

CREATE INDEX IF NOT EXISTS idx_yara_enabled ON yara_rules(enabled);

-- ============================================
-- PERSISTENCE ENTRIES TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS persistence_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id INTEGER NOT NULL,
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    type TEXT NOT NULL, -- registry, startup_folder, scheduled_task, service, cron, systemd
    location TEXT NOT NULL,
    command TEXT NOT NULL,
    hash_value TEXT,
    is_baseline BOOLEAN DEFAULT 0, -- Known good entry
    is_suspicious BOOLEAN DEFAULT 0,
    FOREIGN KEY (device_id) REFERENCES devices(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_persistence_device ON persistence_entries(device_id);
CREATE INDEX IF NOT EXISTS idx_persistence_suspicious ON persistence_entries(is_suspicious);

-- ============================================
-- USER ACCOUNTS TABLE (Mobile App Users)
-- ============================================
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    role TEXT DEFAULT 'user' CHECK(role IN ('admin', 'user'))
);

-- ============================================
-- DEVICE USERS MAPPING (Multi-user support)
-- ============================================
CREATE TABLE IF NOT EXISTS device_users (
    device_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    access_level TEXT DEFAULT 'viewer' CHECK(access_level IN ('owner', 'admin', 'viewer')),
    granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (device_id, user_id),
    FOREIGN KEY (device_id) REFERENCES devices(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- ============================================
-- CONFIGURATION TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS config (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert default configuration
INSERT OR IGNORE INTO config (key, value) VALUES 
    ('scan_interval_hours', '24'),
    ('auto_quarantine', 'true'),
    ('alert_threshold_severity', '7'),
    ('cloud_sync_enabled', 'false'),
    ('network_ids_enabled', 'true');

-- ============================================
-- VIEWS FOR COMMON QUERIES
-- ============================================

-- Active threats (not dismissed)
CREATE VIEW IF NOT EXISTS active_threats AS
SELECT 
    t.*,
    d.hostname,
    d.os
FROM threats t
JOIN devices d ON t.device_id = d.id
WHERE t.dismissed = 0
ORDER BY t.severity DESC, t.detected_at DESC;

-- Device status summary
CREATE VIEW IF NOT EXISTS device_summary AS
SELECT 
    d.id,
    d.hostname,
    d.status,
    d.last_seen,
    COUNT(DISTINCT s.id) as total_scans,
    COUNT(DISTINCT CASE WHEN t.dismissed = 0 THEN t.id END) as active_threats,
    MAX(s.completed_at) as last_scan
FROM devices d
LEFT JOIN scans s ON d.id = s.device_id AND s.status = 'completed'
LEFT JOIN threats t ON d.id = t.device_id
GROUP BY d.id;

-- Recent activity (last 24 hours)
CREATE VIEW IF NOT EXISTS recent_activity AS
SELECT 
    'threat' as activity_type,
    t.detected_at as timestamp,
    d.hostname,
    t.explanation as details
FROM threats t
JOIN devices d ON t.device_id = d.id
WHERE t.detected_at > datetime('now', '-24 hours')
UNION ALL
SELECT 
    'action' as activity_type,
    a.timestamp,
    d.hostname,
    a.action_type || ' on ' || a.target as details
FROM actions a
JOIN devices d ON a.device_id = d.id
WHERE a.timestamp > datetime('now', '-24 hours')
ORDER BY timestamp DESC;

-- ============================================
-- PAIRING TOKENS table
-- ============================================
CREATE TABLE IF NOT EXISTS pairing_tokens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    token TEXT UNIQUE NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    expires_at DATETIME NOT NULL,
    used_at DATETIME,
    created_by INTEGER REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_pairing_tokens_token ON pairing_tokens(token);
