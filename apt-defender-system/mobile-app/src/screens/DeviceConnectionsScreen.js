import React, { useState, useEffect } from 'react';
import {
    View,
    Text,
    FlatList,
    StyleSheet,
    ActivityIndicator,
    RefreshControl,
    Alert
} from 'react-native';
import piClient from '../api/piClient';
import theme from '../theme/greenTheme';

export default function DeviceConnectionsScreen({ route, navigation }) {
    const { deviceId } = route.params;
    const [connections, setConnections] = useState([]);
    const [loading, setLoading] = useState(true);
    const [refreshing, setRefreshing] = useState(false);

    useEffect(() => {
        loadConnections();
    }, [deviceId]);

    const loadConnections = async () => {
        try {
            const response = await piClient.getDeviceConnections(deviceId);
            if (response.success) {
                setConnections(response.data.connections || []);
            }
        } catch (error) {
            console.error('Error loading connections:', error);
            Alert.alert('Error', 'Failed to fetch network connections');
        } finally {
            setLoading(false);
            setRefreshing(false);
        }
    };

    const renderConnectionItem = ({ item }) => (
        <View style={styles.connItem}>
            <View style={styles.connMain}>
                <Text style={styles.connText}>
                    {item.laddr?.ip}:{item.laddr?.port} → {item.raddr?.ip || 'listening'}:{item.raddr?.port || ''}
                </Text>
                <Text style={styles.connProcess}>{item.process_name || 'unknown'} (PID: {item.pid})</Text>
            </View>
            <View style={styles.connStatus}>
                <Text style={[styles.statusBadge, item.status === 'ESTABLISHED' ? styles.statusEstablished : styles.statusOther]}>
                    {item.status}
                </Text>
            </View>
        </View>
    );

    if (loading) {
        return (
            <View style={styles.centerContainer}>
                <ActivityIndicator size="large" color={theme.colors.primary} />
            </View>
        );
    }

    return (
        <View style={styles.container}>
            <View style={styles.header}>
                <Text style={styles.title}>Network Connections</Text>
                <Text style={styles.subtitle}>{connections.length} active connections</Text>
            </View>

            <FlatList
                data={connections}
                keyExtractor={(item, index) => index.toString()}
                renderItem={renderConnectionItem}
                contentContainerStyle={styles.listContent}
                refreshControl={
                    <RefreshControl
                        refreshing={refreshing}
                        onRefresh={() => {
                            setRefreshing(true);
                            loadConnections();
                        }}
                        tintColor={theme.colors.primary}
                    />
                }
                ListEmptyComponent={
                    <View style={styles.emptyContainer}>
                        <Text style={styles.emptyText}>No active connections found</Text>
                    </View>
                }
            />
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
        borderBottomWidth: 1,
        borderBottomColor: theme.colors.primary,
    },
    title: {
        fontSize: theme.typography.fontSize.xl,
        fontWeight: theme.typography.fontWeight.bold,
        color: theme.colors.textPrimary,
    },
    subtitle: {
        fontSize: theme.typography.fontSize.md,
        color: theme.colors.textSecondary,
    },
    listContent: {
        padding: theme.spacing.md,
    },
    connItem: {
        flexDirection: 'row',
        backgroundColor: theme.colors.surface,
        padding: theme.spacing.md,
        borderRadius: theme.borderRadius.md,
        marginBottom: theme.spacing.sm,
        alignItems: 'center',
        borderWidth: 1,
        borderColor: theme.colors.primaryDark,
    },
    connMain: {
        flex: 1,
    },
    connText: {
        fontSize: theme.typography.fontSize.sm,
        fontWeight: 'bold',
        color: theme.colors.textPrimary,
    },
    connProcess: {
        fontSize: theme.typography.fontSize.xs,
        color: theme.colors.textSecondary,
        marginTop: 2,
    },
    connStatus: {
        marginLeft: theme.spacing.md,
    },
    statusBadge: {
        fontSize: 10,
        fontWeight: 'bold',
        paddingHorizontal: 6,
        paddingVertical: 2,
        borderRadius: 4,
        overflow: 'hidden',
    },
    statusEstablished: {
        backgroundColor: theme.colors.success,
        color: '#fff',
    },
    statusOther: {
        backgroundColor: theme.colors.surface,
        color: theme.colors.textSecondary,
        borderWidth: 1,
        borderColor: theme.colors.textSecondary,
    },
    emptyContainer: {
        padding: theme.spacing.xl,
        alignItems: 'center',
    },
    emptyText: {
        color: theme.colors.textSecondary,
    }
});
