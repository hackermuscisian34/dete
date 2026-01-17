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
} from 'react-native';
import piClient from '../api/piClient';
import theme from '../theme/greenTheme';

export default function DeviceDetailScreen({ route, navigation }) {
    const { deviceId } = route.params;
    const [device, setDevice] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadDeviceDetails();
    }, [deviceId]);

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
            await piClient.scanDevice(deviceId);
            Alert.alert('Success', 'Scan started. Results will appear soon.');
        } catch (error) {
            Alert.alert('Error', 'Failed to start scan');
        }
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

            {/* Status Card */}
            <View style={styles.statusCard}>
                <Text style={Styles.sectionTitle}>Status</Text>
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
});
