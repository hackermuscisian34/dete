/**
 * Device Telemetry Screen - Real-time system statistics
 */
import React, { useState, useEffect } from 'react';
import {
    View,
    Text,
    ScrollView,
    StyleSheet,
    ActivityIndicator,
    RefreshControl,
} from 'react-native';
import piClient from '../api/piClient';
import theme from '../theme/greenTheme';

export default function DeviceTelemetryScreen({ route }) {
    const { deviceId } = route.params;
    const [telemetry, setTelemetry] = useState(null);
    const [loading, setLoading] = useState(true);
    const [refreshing, setRefreshing] = useState(false);

    useEffect(() => {
        loadTelemetry();
        // Auto-refresh every 3 seconds
        const interval = setInterval(loadTelemetry, 3000);
        return () => clearInterval(interval);
    }, [deviceId]);

    const loadTelemetry = async () => {
        try {
            const response = await piClient.getDeviceTelemetry(deviceId);
            if (response.success && response.telemetry) {
                setTelemetry(response.telemetry);
            }
        } catch (error) {
            console.error('Error loading telemetry:', error);
        } finally {
            setLoading(false);
            setRefreshing(false);
        }
    };

    const onRefresh = () => {
        setRefreshing(true);
        loadTelemetry();
    };

    const formatUptime = (seconds) => {
        const days = Math.floor(seconds / 86400);
        const hours = Math.floor((seconds % 86400) / 3600);
        const mins = Math.floor((seconds % 3600) / 60);
        return `${days}d ${hours}h ${mins}m`;
    };

    const getUsageColor = (percent) => {
        if (percent >= 90) return theme.colors.danger;
        if (percent >= 70) return theme.colors.warning;
        return theme.colors.success;
    };

    if (loading) {
        return (
            <View style={styles.centerContainer}>
                <ActivityIndicator size="large" color={theme.colors.primary} />
            </View>
        );
    }

    if (!telemetry) {
        return (
            <View style={styles.centerContainer}>
                <Text style={styles.errorText}>Unable to fetch telemetry</Text>
                <Text style={styles.errorSubtext}>
                    Make sure the Helper Service is running on the PC
                </Text>
            </View>
        );
    }

    return (
        <ScrollView
            style={styles.container}
            refreshControl={
                <RefreshControl
                    refreshing={refreshing}
                    onRefresh={onRefresh}
                    tintColor={theme.colors.primary}
                />
            }
        >
            {/* System Info */}
            <View style={styles.card}>
                <Text style={styles.cardTitle}>💻 System Information</Text>
                <View style={styles.infoRow}>
                    <Text style={styles.infoLabel}>Hostname:</Text>
                    <Text style={styles.infoValue}>{telemetry.system.hostname}</Text>
                </View>
                <View style={styles.infoRow}>
                    <Text style={styles.infoLabel}>OS:</Text>
                    <Text style={styles.infoValue}>
                        {telemetry.system.os} ({telemetry.system.platform})
                    </Text>
                </View>
                <View style={styles.infoRow}>
                    <Text style={styles.infoLabel}>Uptime:</Text>
                    <Text style={styles.infoValue}>
                        {formatUptime(telemetry.system.uptime_seconds)}
                    </Text>
                </View>
            </View>

            {/* CPU Usage */}
            <View style={styles.card}>
                <Text style={styles.cardTitle}>⚡ CPU Usage</Text>
                <View style={styles.infoRow}>
                    <Text style={styles.infoLabel}>Cores:</Text>
                    <Text style={styles.infoValue}>{telemetry.cpu.cores}</Text>
                </View>

                <View style={styles.progressContainer}>
                    <View style={styles.progressBar}>
                        <View
                            style={[
                                styles.progressFill,
                                {
                                    width: `${telemetry.cpu.usage_percent}%`,
                                    backgroundColor: getUsageColor(telemetry.cpu.usage_percent),
                                },
                            ]}
                        />
                    </View>
                    <Text style={[styles.percentText, { color: getUsageColor(telemetry.cpu.usage_percent) }]}>
                        {Math.round(telemetry.cpu.usage_percent)}%
                    </Text>
                </View>
            </View>

            {/* Memory Usage */}
            <View style={styles.card}>
                <Text style={styles.cardTitle}>🧠 Memory Usage</Text>
                <View style={styles.infoRow}>
                    <Text style={styles.infoLabel}>Total:</Text>
                    <Text style={styles.infoValue}>
                        {(telemetry.memory.total_mb / 1024).toFixed(1)} GB
                    </Text>
                </View>
                <View style={styles.infoRow}>
                    <Text style={styles.infoLabel}>Used:</Text>
                    <Text style={styles.infoValue}>
                        {(telemetry.memory.used_mb / 1024).toFixed(1)} GB
                    </Text>
                </View>
                <View style={styles.infoRow}>
                    <Text style={styles.infoLabel}>Available:</Text>
                    <Text style={styles.infoValue}>
                        {(telemetry.memory.available_mb / 1024).toFixed(1)} GB
                    </Text>
                </View>

                <View style={styles.progressContainer}>
                    <View style={styles.progressBar}>
                        <View
                            style={[
                                styles.progressFill,
                                {
                                    width: `${telemetry.memory.usage_percent}%`,
                                    backgroundColor: getUsageColor(telemetry.memory.usage_percent),
                                },
                            ]}
                        />
                    </View>
                    <Text style={[styles.percentText, { color: getUsageColor(telemetry.memory.usage_percent) }]}>
                        {Math.round(telemetry.memory.usage_percent)}%
                    </Text>
                </View>
            </View>

            {/* Disk Usage */}
            <View style={styles.card}>
                <Text style={styles.cardTitle}>💾 Disk Usage (C:)</Text>
                <View style={styles.infoRow}>
                    <Text style={styles.infoLabel}>Total:</Text>
                    <Text style={styles.infoValue}>{telemetry.disk.total_gb} GB</Text>
                </View>
                <View style={styles.infoRow}>
                    <Text style={styles.infoLabel}>Used:</Text>
                    <Text style={styles.infoValue}>{telemetry.disk.used_gb} GB</Text>
                </View>
                <View style={styles.infoRow}>
                    <Text style={styles.infoLabel}>Free:</Text>
                    <Text style={styles.infoValue}>{telemetry.disk.free_gb} GB</Text>
                </View>

                <View style={styles.progressContainer}>
                    <View style={styles.progressBar}>
                        <View
                            style={[
                                styles.progressFill,
                                {
                                    width: `${telemetry.disk.usage_percent}%`,
                                    backgroundColor: getUsageColor(telemetry.disk.usage_percent),
                                },
                            ]}
                        />
                    </View>
                    <Text style={[styles.percentText, { color: getUsageColor(telemetry.disk.usage_percent) }]}>
                        {Math.round(telemetry.disk.usage_percent)}%
                    </Text>
                </View>
            </View>

            {/* Auto-refresh indicator */}
            <View style={styles.refreshIndicator}>
                <Text style={styles.refreshText}>🔄 Auto-refreshes every 3 seconds</Text>
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
        padding: theme.spacing.xl,
    },
    card: {
        backgroundColor: theme.colors.surface,
        margin: theme.spacing.md,
        padding: theme.spacing.lg,
        borderRadius: theme.borderRadius.lg,
        borderWidth: 1,
        borderColor: theme.colors.primaryDark,
    },
    cardTitle: {
        fontSize: theme.typography.fontSize.xl,
        fontWeight: theme.typography.fontWeight.bold,
        color: theme.colors.primary,
        marginBottom: theme.spacing.md,
    },
    infoRow: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        marginBottom: theme.spacing.sm,
    },
    infoLabel: {
        fontSize: theme.typography.fontSize.md,
        color: theme.colors.textSecondary,
    },
    infoValue: {
        fontSize: theme.typography.fontSize.md,
        fontWeight: theme.typography.fontWeight.bold,
        color: theme.colors.textPrimary,
    },
    progressContainer: {
        marginTop: theme.spacing.md,
    },
    progressBar: {
        height: 24,
        backgroundColor: theme.colors.primaryDark,
        borderRadius: 12,
        overflow: 'hidden',
        marginBottom: theme.spacing.xs,
    },
    progressFill: {
        height: '100%',
        justifyContent: 'center',
        alignItems: 'center',
    },
    percentText: {
        fontSize: theme.typography.fontSize.xl,
        fontWeight: theme.typography.fontWeight.bold,
        textAlign: 'center',
        marginTop: theme.spacing.xs,
    },
    errorText: {
        fontSize: theme.typography.fontSize.lg,
        color: theme.colors.danger,
        textAlign: 'center',
        marginBottom: theme.spacing.sm,
    },
    errorSubtext: {
        fontSize: theme.typography.fontSize.md,
        color: theme.colors.textSecondary,
        textAlign: 'center',
    },
    refreshIndicator: {
        padding: theme.spacing.md,
        alignItems: 'center',
    },
    refreshText: {
        color: theme.colors.textSecondary,
        fontSize: theme.typography.fontSize.sm,
    },
});
