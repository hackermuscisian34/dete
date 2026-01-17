/**
 * Devices Screen - List all paired devices
 */
import React, { useState, useEffect } from 'react';
import {
    View,
    Text,
    FlatList,
    TouchableOpacity,
    StyleSheet,
    RefreshControl,
    ActivityIndicator,
} from 'react';
import piClient from '../api/piClient';
import DeviceCard from '../components/DeviceCard';
import theme from '../theme/greenTheme';

export default function DevicesScreen({ navigation }) {
    const [devices, setDevices] = useState([]);
    const [loading, setLoading] = useState(true);
    const [refreshing, setRefreshing] = useState(false);

    useEffect(() => {
        loadDevices();
    }, []);

    const loadDevices = async () => {
        try {
            const response = await piClient.getDevices();
            if (response.success) {
                setDevices(response.data.devices || []);
            }
        } catch (error) {
            console.error('Error loading devices:', error);
        } finally {
            setLoading(false);
            setRefreshing(false);
        }
    };

    const onRefresh = () => {
        setRefreshing(true);
        loadDevices();
    };

    const handleDevicePress = (device) => {
        navigation.navigate('DeviceDetail', { deviceId: device.id });
    };

    if (loading) {
        return (
            <View style={styles.centerContainer}>
                <ActivityIndicator size="large" color={theme.colors.primary} />
            </View>
        );
    }

    return (
        <View style={styles.container}>
            {/* Header */}
            <View style={styles.header}>
                <Text style={styles.title}>My Devices</Text>
                <Text style={styles.subtitle}>
                    {devices.length} {devices.length === 1 ? 'device' : 'devices'} protected
                </Text>
            </View>

            {/* Device List */}
            {devices.length === 0 ? (
                <View style={styles.emptyContainer}>
                    <Text style={styles.emptyText}>No devices paired yet</Text>
                    <Text style={styles.emptySubtext}>
                        Scan the QR code on your Raspberry Pi to add a device
                    </Text>
                    <TouchableOpacity style={styles.addButton}>
                        <Text style={styles.addButtonText}>Add Device</Text>
                    </TouchableOpacity>
                </View>
            ) : (
                <FlatList
                    data={devices}
                    keyExtractor={(item) => item.id.toString()}
                    renderItem={({ item }) => (
                        <DeviceCard device={item} onPress={() => handleDevicePress(item)} />
                    )}
                    contentContainerStyle={styles.listContent}
                    refreshControl={
                        <RefreshControl
                            refreshing={refreshing}
                            onRefresh={onRefresh}
                            tintColor={theme.colors.primary}
                        />
                    }
                />
            )}
        </View>
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
    },
    title: {
        fontSize: theme.typography.fontSize.xxl,
        fontWeight: theme.typography.fontWeight.bold,
        color: theme.colors.textPrimary,
        marginBottom: theme.spacing.xs,
    },
    subtitle: {
        fontSize: theme.typography.fontSize.md,
        color: theme.colors.textSecondary,
    },
    listContent: {
        padding: theme.spacing.md,
    },
    emptyContainer: {
        flex: 1,
        justifyContent: 'center',
        alignItems: 'center',
        padding: theme.spacing.xl,
    },
    emptyText: {
        fontSize: theme.typography.fontSize.lg,
        color: theme.colors.textPrimary,
        marginBottom: theme.spacing.sm,
        textAlign: 'center',
    },
    emptySubtext: {
        fontSize: theme.typography.fontSize.md,
        color: theme.colors.textSecondary,
        textAlign: 'center',
        marginBottom: theme.spacing.xl,
    },
    addButton: {
        backgroundColor: theme.colors.primary,
        paddingHorizontal: theme.spacing.xl,
        paddingVertical: theme.spacing.md,
        borderRadius: theme.borderRadius.md,
        ...theme.shadows.md,
    },
    addButtonText: {
        color: theme.colors.textOnPrimary,
        fontSize: theme.typography.fontSize.lg,
        fontWeight: theme.typography.fontWeight.bold,
    },
});
