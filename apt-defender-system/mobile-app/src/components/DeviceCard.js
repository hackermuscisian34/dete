/**
 * Device Card Component
 */
import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import theme from '../theme/greenTheme';

export default function DeviceCard({ device, onPress }) {
    const getStatusColor = (status) => {
        switch (status) {
            case 'online':
                return theme.colors.success;
            case 'threat':
                return theme.colors.danger;
            case 'offline':
                return theme.colors.textMuted;
            default:
                return theme.colors.warning;
        }
    };

    const getStatusText = (status) => {
        switch (status) {
            case 'online':
                return 'SAFE';
            case 'threat':
                return 'THREAT';
            case 'offline':
                return 'OFFLINE';
            case 'isolated':
                return 'ISOLATED';
            default:
                return status.toUpperCase();
        }
    };

    const getOSIcon = (os) => {
        // Simple text icons for now
        switch (os.toLowerCase()) {
            case 'windows':
                return '🪟';
            case 'linux':
                return '🐧';
            case 'macos':
                return '🍎';
            default:
                return '💻';
        }
    };

    return (
        <TouchableOpacity style={styles.card} onPress={onPress}>
            {/* Header */}
            <View style={styles.header}>
                <View style={styles.titleRow}>
                    <Text style={styles.icon}>{getOSIcon(device.os)}</Text>
                    <Text style={styles.hostname}>{device.hostname}</Text>
                </View>
                <View style={[styles.statusBadge, { backgroundColor: getStatusColor(device.status) }]}>
                    <Text style={styles.statusText}>{getStatusText(device.status)}</Text>
                </View>
            </View>

            {/* Info */}
            <View style={styles.info}>
                <Text style={styles.infoText}>
                    Last scan: {device.last_scan ? formatTime(device.last_scan) : 'Never'}
                </Text>
                <Text style={styles.infoText}>
                    Threats: <Text style={styles.threatCount}>{device.active_threats || 0}</Text>
                </Text>
            </View>

            {/* Threat Warning */}
            {device.active_threats > 0 && (
                <View style={styles.warningBox}>
                    <Text style={styles.warningText}>
                        ⚠️ {device.active_threats} active threat{device.active_threats !== 1 ? 's' : ''}
                    </Text>
                </View>
            )}
        </TouchableOpacity>
    );
}

function formatTime(timestamp) {
    const now = new Date();
    const time = new Date(timestamp);
    const diff = Math.floor((now - time) / 1000); // seconds

    if (diff < 60) return `${diff} seconds ago`;
    if (diff < 3600) return `${Math.floor(diff / 60)} minutes ago`;
    if (diff < 86400) return `${Math.floor(diff / 3600)} hours ago`;
    return `${Math.floor(diff / 86400)} days ago`;
}

const styles = StyleSheet.create({
    card: {
        backgroundColor: theme.colors.surface,
        borderRadius: theme.borderRadius.lg,
        padding: theme.spacing.md,
        marginBottom: theme.spacing.md,
        borderWidth: 1,
        borderColor: theme.colors.primaryDark,
        ...theme.shadows.md,
    },
    header: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: theme.spacing.md,
    },
    titleRow: {
        flexDirection: 'row',
        alignItems: 'center',
        flex: 1,
    },
    icon: {
        fontSize: 24,
        marginRight: theme.spacing.sm,
    },
    hostname: {
        fontSize: theme.typography.fontSize.lg,
        fontWeight: theme.typography.fontWeight.bold,
        color: theme.colors.textPrimary,
        flex: 1,
    },
    statusBadge: {
        paddingHorizontal: theme.spacing.md,
        paddingVertical: theme.spacing.xs,
        borderRadius: theme.borderRadius.full,
    },
    statusText: {
        color: theme.colors.textOnPrimary,
        fontSize: theme.typography.fontSize.xs,
        fontWeight: theme.typography.fontWeight.bold,
    },
    info: {
        flexDirection: 'row',
        justifyContent: 'space-between',
    },
    infoText: {
        fontSize: theme.typography.fontSize.sm,
        color: theme.colors.textSecondary,
    },
    threatCount: {
        color: theme.colors.danger,
        fontWeight: theme.typography.fontWeight.bold,
    },
    warningBox: {
        marginTop: theme.spacing.md,
        backgroundColor: theme.colors.danger + '20', // 20% opacity
        padding: theme.spacing.sm,
        borderRadius: theme.borderRadius.sm,
        borderLeftWidth: 4,
        borderLeftColor: theme.colors.danger,
    },
    warningText: {
        color: theme.colors.danger,
        fontSize: theme.typography.fontSize.sm,
        fontWeight: theme.typography.fontWeight.medium,
    },
});
