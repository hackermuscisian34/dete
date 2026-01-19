/**
 * Device Detail Screen - Full device information and actions
 */
import React, { useState, useEffect } from 'react';
import {
    View,
    Text,
    ScrollView,
    TouchableOpacity,
    StyleSheet,
    Alert,
    ActivityIndicator,
    Linking,
} from 'react-native';
import piClient from '../api/piClient';
import theme from '../theme/greenTheme';

export default function DeviceDetailScreen({ route, navigation }) {
    const { deviceId } = route.params;
    const [device, setDevice] = useState(null);
    const [loading, setLoading] = useState(true);
    const [scanStatus, setScanStatus] = useState(null);
    const [polling, setPolling] = useState(false);

    useEffect(() => {
        loadDeviceDetails();
        checkScanStatus();
    }, [deviceId]);

    useEffect(() => {
        let interval;
        if (polling) {
            interval = setInterval(checkScanStatus, 3000); // Poll every 3 seconds
        }
        return () => clearInterval(interval);
    }, [polling]);

    const checkScanStatus = async () => {
        try {
            const response = await piClient.getScanStatus(deviceId);
            if (response.success && response.data) {
                setScanStatus(response.data);
                if (response.data.status === 'running') {
                    setPolling(true);
                } else {
                    setPolling(false);
                }
            }
        } catch (error) {
            console.error('Error checking scan status:', error);
            setPolling(false);
        }
    };

    const loadDeviceDetails = async () => {
        try {
            const response = await piClient.getDevice(deviceId);
            if (response.success) {
                setDevice(response.data);
            }
        } catch (error) {
            console.error('Error loading device:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleScanNow = async () => {
        try {
            const response = await piClient.scanDevice(deviceId);
            if (response.success) {
                Alert.alert('Success', 'Scan started. tracking progress...');
                setPolling(true);
                checkScanStatus();
            }
        } catch (error) {
            Alert.alert('Error', 'Failed to start scan');
        }
    };

    const handleViewReport = () => {
        if (!scanStatus?.scan_id) return;
        const url = piClient.getScanReportUrl(deviceId, scanStatus.scan_id);
        Linking.openURL(url);
    };

    const formatTime = (seconds) => {
        if (!seconds || seconds <= 0) return 'calculating...';
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${mins}m ${secs}s remaining`;
    };

    const handleLockDevice = () => {
        Alert.alert(
            'Lock Device',
            'This will lock the computer screen. Continue?',
            [
                { text: 'Cancel', style: 'cancel' },
                {
                    text: 'Lock',
                    style: 'destructive',
                    onPress: async () => {
                        try {
                            await piClient.lockDevice(deviceId);
                            Alert.alert('Success', 'Device locked');
                        } catch (error) {
                            Alert.alert('Error', 'Failed to lock device');
                        }
                    },
                },
            ]
        );
    };

    const handleIsolateDevice = () => {
        Alert.alert(
            'Block Network',
            'This will disconnect the computer from all networks. The computer will be offline until you restore network access. Continue?',
            [
                { text: 'Cancel', style: 'cancel' },
                {
                    text: 'Block Network',
                    style: 'destructive',
                    onPress: async () => {
                        try {
                            await piClient.isolateDevice(deviceId);
                            Alert.alert('Success', 'Network access blocked');
                            loadDeviceDetails(); // Reload to show new status
                        } catch (error) {
                            Alert.alert('Error', 'Failed to block network');
                        }
                    },
                },
            ]
        );
    };

    const handleShutdown = () => {
        Alert.alert(
            'Shutdown Device',
            'This will shut down the computer in 60 seconds. Continue?',
            [
                { text: 'Cancel', style: 'cancel' },
                {
                    text: 'Shutdown',
                    style: 'destructive',
                    onPress: async () => {
                        try {
                            await piClient.shutdownDevice(deviceId, 60);
                            Alert.alert('Success', 'Shutdown scheduled');
                        } catch (error) {
                            Alert.alert('Error', 'Failed to schedule shutdown');
                        }
                    },
                },
            ]
        );
    };

    const handleDeleteDevice = () => {
        Alert.alert(
            'Delete Device',
            'This will remove this device from your account. You will need to re-pair it to monitor it again. Continue?',
            [
                { text: 'Cancel', style: 'cancel' },
                {
                    text: 'Delete',
                    style: 'destructive',
                    onPress: async () => {
                        try {
                            const response = await piClient.unpairDevice(deviceId);
                            if (response.success) {
                                Alert.alert('Deleted', 'Device removed successfully');
                                navigation.navigate('Devices'); // Go back to list
                            }
                        } catch (error) {
                            Alert.alert('Error', 'Failed to delete device');
                        }
                    },
                },
            ]
        );
    };

    if (loading) {
        return (
            <View style={styles.centerContainer}>
                <ActivityIndicator size="large" color={theme.colors.primary} />
            </View>
        );
    }

    if (!device) {
        return (
            <View style={styles.centerContainer}>
                <Text style={styles.errorText}>Device not found</Text>
            </View>
        );
    }

    return (
        <ScrollView style={styles.container}>
            {/* Header */}
            <View style={styles.header}>
                <Text style={styles.hostname}>{device.hostname}</Text>
                <Text style={styles.osInfo}>
                    {device.os_version} • {device.ip_address}
                </Text>
            </View>

            {/* Scan Progress (Only when active or recently completed) */}
            {scanStatus && (
                <View style={[styles.statusCard, { borderColor: scanStatus.status === 'running' ? theme.colors.primary : theme.colors.primaryDark }]}>
                    <Text style={styles.sectionTitle}>
                        {scanStatus.status === 'running' ? '🔍 Scanning Now...' : '✅ Latest Scan Result'}
                    </Text>

                    {scanStatus.status === 'running' && (
                        <View style={styles.progressContainer}>
                            <View style={styles.progressBar}>
                                <View
                                    style={[
                                        styles.progressFill,
                                        { width: `${(scanStatus.files_checked / (scanStatus.total_files || 1)) * 100}%` }
                                    ]}
                                />
                            </View>
                            <Text style={styles.progressText}>
                                {scanStatus.files_checked} / {scanStatus.total_files} files checked
                            </Text>
                            <Text style={styles.timeText}>
                                {formatTime(scanStatus.remaining_seconds)}
                            </Text>
                        </View>
                    )}

                    <View style={styles.statusRow}>
                        <Text style={styles.statusLabel}>Detected Threats:</Text>
                        <Text style={[styles.statusValue, { color: scanStatus.threats_found > 0 ? theme.colors.danger : theme.colors.success }]}>
                            {scanStatus.threats_found}
                        </Text>
                    </View>

                    {scanStatus.status === 'completed' && (
                        <View style={{ flexDirection: 'row', justifyContent: 'space-between', marginTop: theme.spacing.md }}>
                            <TouchableOpacity style={[styles.reportButton, { flex: 1, marginRight: 5 }]} onPress={handleViewReport}>
                                <Text style={styles.reportButtonText}>📄 HTML Report</Text>
                            </TouchableOpacity>
                            <TouchableOpacity
                                style={[styles.reportButton, { flex: 1, marginLeft: 5 }]}
                                onPress={() => Linking.openURL(`${piClient.getScanReportUrl(deviceId, scanStatus.scan_id)}/log`)}
                            >
                                <Text style={styles.reportButtonText}>📝 Log Report</Text>
                            </TouchableOpacity>
                        </View>
                    )}
                </View>
            )}

            {/* Status Card */}
            <View style={styles.statusCard}>
                <Text style={styles.sectionTitle}>Status</Text>
                <View style={styles.statusRow}>
                    <Text style={styles.statusLabel}>Protection:</Text>
                    <Text style={[styles.statusValue, { color: theme.colors.success }]}>
                        ACTIVE
                    </Text>
                </View>
                <View style={styles.statusRow}>
                    <Text style={styles.statusLabel}>Active Threats:</Text>
                    <Text
                        style={[
                            styles.statusValue,
                            { color: device.active_threats > 0 ? theme.colors.danger : theme.colors.success },
                        ]}
                    >
                        {device.active_threats || 0}
                    </Text>
                </View>
                <View style={styles.statusRow}>
                    <Text style={styles.statusLabel}>Total Scans:</Text>
                    <Text style={styles.statusValue}>{device.total_scans || 0}</Text>
                </View>
            </View>

            {/* Main Actions */}
            <View style={styles.actionsCard}>
                <Text style={styles.sectionTitle}>Actions</Text>

                <TouchableOpacity style={styles.primaryButton} onPress={handleScanNow}>
                    <Text style={styles.primaryButtonText}>🔍 Scan Now</Text>
                </TouchableOpacity>

                <TouchableOpacity style={styles.warningButton} onPress={handleLockDevice}>
                    <Text style={styles.buttonText}>🔒 Lock Device</Text>
                </TouchableOpacity>

                <TouchableOpacity style={styles.warningButton} onPress={handleIsolateDevice}>
                    <Text style={styles.buttonText}>🚫 Block Network</Text>
                </TouchableOpacity>

                <TouchableOpacity style={styles.dangerButton} onPress={handleShutdown}>
                    <Text style={styles.buttonText}>⏻ Shutdown</Text>
                </TouchableOpacity>

                <View style={{ marginTop: theme.spacing.xl, borderTopWidth: 1, borderTopColor: theme.colors.primaryDark, paddingTop: theme.spacing.md }}>
                    <TouchableOpacity style={styles.deleteButton} onPress={handleDeleteDevice}>
                        <Text style={styles.buttonText}>🗑️ Delete Device</Text>
                    </TouchableOpacity>
                </View>
            </View>

            {/* Quick Links */}
            <View style={styles.linksCard}>
                <Text style={styles.sectionTitle}>More</Text>

                <TouchableOpacity
                    style={styles.linkButton}
                    onPress={() => navigation.navigate('DeviceTimeline', { deviceId })}
                >
                    <Text style={styles.linkText}>View Timeline →</Text>
                </TouchableOpacity>

                <TouchableOpacity
                    style={styles.linkButton}
                    onPress={() => navigation.navigate('DeviceProcesses', { deviceId })}
                >
                    <Text style={styles.linkText}>Running Programs →</Text>
                </TouchableOpacity>

                <TouchableOpacity
                    style={styles.linkButton}
                    onPress={() => navigation.navigate('DeviceConnections', { deviceId })}
                >
                    <Text style={styles.linkText}>Network Connections →</Text>
                </TouchableOpacity>
            </View>
        </ScrollView>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: theme.colors.background,
    },
    centerContainer: {
        flex: 1,
        justifyContent: 'center',
        alignItems: 'center',
        backgroundColor: theme.colors.background,
    },
    header: {
        padding: theme.spacing.xl,
        backgroundColor: theme.colors.surface,
        borderBottomWidth: 1,
        borderBottomColor: theme.colors.primary,
    },
    hostname: {
        fontSize: theme.typography.fontSize.xxl,
        fontWeight: theme.typography.fontWeight.bold,
        color: theme.colors.textPrimary,
        marginBottom: theme.spacing.xs,
    },
    osInfo: {
        fontSize: theme.typography.fontSize.md,
        color: theme.colors.textSecondary,
    },
    statusCard: {
        backgroundColor: theme.colors.surface,
        margin: theme.spacing.md,
        padding: theme.spacing.md,
        borderRadius: theme.borderRadius.lg,
        borderWidth: 1,
        borderColor: theme.colors.primaryDark,
    },
    actionsCard: {
        backgroundColor: theme.colors.surface,
        margin: theme.spacing.md,
        padding: theme.spacing.md,
        borderRadius: theme.borderRadius.lg,
        borderWidth: 1,
        borderColor: theme.colors.primaryDark,
    },
    linksCard: {
        backgroundColor: theme.colors.surface,
        margin: theme.spacing.md,
        marginBottom: theme.spacing.xxl,
        padding: theme.spacing.md,
        borderRadius: theme.borderRadius.lg,
        borderWidth: 1,
        borderColor: theme.colors.primaryDark,
    },
    sectionTitle: {
        fontSize: theme.typography.fontSize.lg,
        fontWeight: theme.typography.fontWeight.bold,
        color: theme.colors.primary,
        marginBottom: theme.spacing.md,
    },
    statusRow: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        marginBottom: theme.spacing.sm,
    },
    statusLabel: {
        fontSize: theme.typography.fontSize.md,
        color: theme.colors.textSecondary,
    },
    statusValue: {
        fontSize: theme.typography.fontSize.md,
        fontWeight: theme.typography.fontWeight.bold,
        color: theme.colors.textPrimary,
    },
    primaryButton: {
        backgroundColor: theme.colors.primary,
        padding: theme.spacing.md,
        borderRadius: theme.borderRadius.md,
        alignItems: 'center',
        marginBottom: theme.spacing.sm,
        ...theme.shadows.md,
    },
    primaryButtonText: {
        color: theme.colors.textOnPrimary,
        fontSize: theme.typography.fontSize.lg,
        fontWeight: theme.typography.fontWeight.bold,
    },
    warningButton: {
        backgroundColor: theme.colors.warning,
        padding: theme.spacing.md,
        borderRadius: theme.borderRadius.md,
        alignItems: 'center',
        marginBottom: theme.spacing.sm,
    },
    dangerButton: {
        backgroundColor: theme.colors.danger,
        padding: theme.spacing.md,
        borderRadius: theme.borderRadius.md,
        alignItems: 'center',
    },
    deleteButton: {
        backgroundColor: '#440000',
        padding: theme.spacing.md,
        borderRadius: theme.borderRadius.md,
        alignItems: 'center',
        borderWidth: 1,
        borderColor: theme.colors.danger,
    },
    buttonText: {
        color: theme.colors.textOnPrimary,
        fontSize: theme.typography.fontSize.lg,
        fontWeight: theme.typography.fontWeight.bold,
    },
    linkButton: {
        paddingVertical: theme.spacing.md,
        borderBottomWidth: 1,
        borderBottomColor: theme.colors.primaryDark,
    },
    linkText: {
        fontSize: theme.typography.fontSize.md,
        color: theme.colors.primaryLight,
    },
    errorText: {
        fontSize: theme.typography.fontSize.lg,
        color: theme.colors.textSecondary,
    },
    progressContainer: {
        marginVertical: theme.spacing.md,
    },
    progressBar: {
        height: 10,
        backgroundColor: theme.colors.primaryDark,
        borderRadius: 5,
        overflow: 'hidden',
        marginBottom: theme.spacing.xs,
    },
    progressFill: {
        height: '100%',
        backgroundColor: theme.colors.primary,
    },
    progressText: {
        fontSize: theme.typography.fontSize.sm,
        color: theme.colors.textSecondary,
        textAlign: 'center',
    },
    timeText: {
        fontSize: theme.typography.fontSize.sm,
        color: theme.colors.primaryLight,
        textAlign: 'center',
        fontWeight: 'bold',
        marginTop: 4,
    },
    reportButton: {
        backgroundColor: 'transparent',
        borderWidth: 1,
        borderColor: theme.colors.primary,
        padding: theme.spacing.sm,
        borderRadius: theme.borderRadius.md,
        alignItems: 'center',
        marginTop: theme.spacing.md,
    },
    reportButtonText: {
        color: theme.colors.primary,
        fontWeight: 'bold',
    },
});
