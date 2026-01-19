/**
 * Pi API Client - Interface to Raspberry Pi detection agent
 */
import axios from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';

const API_BASE_URL = 'http://10.232.50.53:8443/api/v1'; // Updated to match PC IP

class PiAPIClient {
    constructor() {
        this.client = axios.create({
            baseURL: API_BASE_URL,
            timeout: 30000,
            headers: {
                'Content-Type': 'application/json',
            },
        });

        // Add authorization header interceptor
        this.client.interceptors.request.use(async (config) => {
            const token = await this.getToken();
            if (token) {
                config.headers.Authorization = `Bearer ${token}`;
            }
            return config;
        });

        // Response interceptor for error handling
        this.client.interceptors.response.use(
            (response) => response.data,
            (error) => {
                if (error.response?.status === 401) {
                    // Token expired, clear storage
                    this.clearToken();
                }
                throw error;
            }
        );
    }

    // Token management
    async setToken(token) {
        await AsyncStorage.setItem('auth_token', token);
    }

    async getToken() {
        return await AsyncStorage.getItem('auth_token');
    }

    async clearToken() {
        await AsyncStorage.removeItem('auth_token');
        await AsyncStorage.removeItem('user_data');
    }

    async setUser(user) {
        await AsyncStorage.setItem('user_data', JSON.stringify(user));
    }

    async getUser() {
        const user = await AsyncStorage.getItem('user_data');
        return user ? JSON.parse(user) : null;
    }

    // Authentication
    async login(email, password) {
        const response = await this.client.post('/auth/login', {
            email,
            password,
        });

        if (response.success && response.data.access_token) {
            await this.setToken(response.data.access_token);
            await this.setUser(response.data.user);
        }

        return response;
    }

    async register(email, password) {
        return await this.client.post('/auth/register', {
            email,
            password,
        });
    }
    async pairDevice(pairingToken, deviceHostname) {
        const response = await this.client.post('/auth/pair', {
            pairing_token: pairingToken,
            device_hostname: deviceHostname,
        });

        if (response.success && response.data.access_token) {
            await this.setToken(response.data.access_token);
        }

        return response;
    }

    async refreshToken() {
        const response = await this.client.post('/auth/refresh');
        if (response.success && response.data.access_token) {
            await this.setToken(response.data.access_token);
        }
        return response;
    }

    async generatePairingCode() {
        return await this.client.post('/auth/generate-pairing-code');
    }

    // Devices
    async getDevices() {
        return await this.client.get('/devices');
    }

    async getDevice(deviceId) {
        return await this.client.get(`/devices/${deviceId}`);
    }

    async scanDevice(deviceId, scanType = 'full') {
        return await this.client.post(`/devices/${deviceId}/scan`, { scan_type: scanType });
    }

    async getScanStatus(deviceId) {
        return await this.client.get(`/devices/${deviceId}/scan/status`);
    }

    getScanReportUrl(deviceId, scanId) {
        return `${API_BASE_URL}/devices/${deviceId}/scan/${scanId}/report`;
    }

    async getDeviceProcesses(deviceId) {
        return await this.client.get(`/devices/${deviceId}/processes`);
    }

    async getDeviceConnections(deviceId) {
        return await this.client.get(`/devices/${deviceId}/connections`);
    }

    async getDeviceTimeline(deviceId, limit = 100) {
        return await this.client.get(`/devices/${deviceId}/timeline?limit=${limit}`);
    }

    async unpairDevice(deviceId) {
        return await this.client.delete(`/devices/${deviceId}`);
    }

    // Threats
    async getThreats(filters = {}) {
        const params = new URLSearchParams(filters).toString();
        return await this.client.get(`/threats?${params}`);
    }

    async getThreat(threatId) {
        return await this.client.get(`/threats/${threatId}`);
    }

    async dismissThreat(threatId, reason) {
        return await this.client.post(`/threats/${threatId}/dismiss`, { reason });
    }

    async getThreatStats() {
        return await this.client.get('/threats/stats/summary');
    }

    // Actions
    async killProcess(deviceId, pid) {
        return await this.client.post(`/devices/${deviceId}/actions/kill`, { pid });
    }

    async quarantineFile(deviceId, path, reason) {
        return await this.client.post(`/devices/${deviceId}/actions/quarantine`, {
            path,
            reason,
        });
    }

    async lockDevice(deviceId) {
        return await this.client.post(`/devices/${deviceId}/actions/lock`, {});
    }

    async shutdownDevice(deviceId, delaySeconds = 60) {
        return await this.client.post(`/devices/${deviceId}/actions/shutdown`, {
            delay_seconds: delaySeconds,
        });
    }

    async isolateDevice(deviceId) {
        return await this.client.post(`/devices/${deviceId}/actions/isolate`, {});
    }

    async restoreNetwork(deviceId) {
        return await this.client.post(`/devices/${deviceId}/actions/restore-network`, {});
    }

    async getActionHistory(deviceId, limit = 50) {
        return await this.client.get(`/devices/${deviceId}/actions/history?limit=${limit}`);
    }

    // System
    async getSystemStatus() {
        return await this.client.get('/system/status');
    }

    async getAlerts() {
        return await this.client.get('/system/alerts');
    }

    async getDashboard() {
        return await this.client.get('/system/dashboard');
    }

    async getConfig() {
        return await this.client.get('/system/config');
    }

    async updateConfig(config) {
        return await this.client.put('/system/config', config);
    }
}

export default new PiAPIClient();
