import React, { useState, useEffect } from 'react';
import {
    View,
    Text,
    FlatList,
    StyleSheet,
    ActivityIndicator,
    RefreshControl,
    TouchableOpacity,
    Alert
} from 'react-native';
import piClient from '../api/piClient';
import theme from '../theme/greenTheme';

export default function DeviceProcessesScreen({ route, navigation }) {
    const { deviceId } = route.params;
    const [processes, setProcesses] = useState([]);
    const [loading, setLoading] = useState(true);
    const [refreshing, setRefreshing] = useState(false);

    useEffect(() => {
        loadProcesses();
    }, [deviceId]);

    const loadProcesses = async () => {
        try {
            const response = await piClient.getDeviceProcesses(deviceId);
            if (response.success) {
                // The API returns { success: true, data: { processes: [...] } }
                setProcesses(response.data.processes || []);
            }
        } catch (error) {
            console.error('Error loading processes:', error);
            Alert.alert('Error', 'Failed to fetch processes from device. Make sure the laptop is online.');
        } finally {
            setLoading(false);
            setRefreshing(false);
        }
    };

    const handleKillProcess = (pid, name) => {
        Alert.alert(
            'Kill Process',
            `Are you sure you want to terminate ${name} (PID: ${pid})?`,
            [
                { text: 'Cancel', style: 'cancel' },
                {
                    text: 'Kill',
                    style: 'destructive',
                    onPress: async () => {
                        try {
                            const response = await piClient.killProcess(deviceId, pid);
                            if (response.success) {
                                Alert.alert('Success', 'Kill command sent');
                                loadProcesses();
                            }
                        } catch (error) {
                            Alert.alert('Error', 'Failed to kill process');
                        }
                    }
                }
            ]
        );
    };

    const renderProcessItem = ({ item }) => (
        <View style={styles.processItem}>
            <View style={styles.processMain}>
                <Text style={styles.processName}>{item.name}</Text>
                <Text style={styles.processPid}>PID: {item.pid} • User: {item.username || 'unknown'}</Text>
            </View>
            <View style={styles.processDetails}>
                <Text style={styles.processStat}>CPU: {item.cpu_percent}%</Text>
                <Text style={styles.processStat}>Mem: {item.memory_percent?.toFixed(1)}%</Text>
            </View>
            <TouchableOpacity
                style={styles.killButton}
                onPress={() => handleKillProcess(item.pid, item.name)}
            >
                <Text style={styles.killButtonText}>Kill</Text>
            </TouchableOpacity>
        </View>
    );

    if (loading) {
        return (
            <View style={styles.centerContainer}>
                <ActivityIndicator size="large" color={theme.colors.primary} />
                <Text style={styles.loadingText}>Fetching processes...</Text>
            </View>
        );
    }

    return (
        <View style={styles.container}>
            <View style={styles.header}>
                <Text style={styles.title}>Running Programs</Text>
                <Text style={styles.subtitle}>{processes.length} active processes</Text>
            </View>

            <FlatList
                data={processes}
                keyExtractor={(item) => item.pid.toString()}
                renderItem={renderProcessItem}
                contentContainerStyle={styles.listContent}
                refreshControl={
                    <RefreshControl
                        refreshing={refreshing}
                        onRefresh={() => {
                            setRefreshing(true);
                            loadProcesses();
                        }}
                        tintColor={theme.colors.primary}
                    />
                }
                ListEmptyComponent={
                    <View style={styles.emptyContainer}>
                        <Text style={styles.emptyText}>No processes found or device is unreachable</Text>
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
    processItem: {
        flexDirection: 'row',
        backgroundColor: theme.colors.surface,
        padding: theme.spacing.md,
        borderRadius: theme.borderRadius.md,
        marginBottom: theme.spacing.sm,
        alignItems: 'center',
        borderWidth: 1,
        borderColor: theme.colors.primaryDark,
    },
    processMain: {
        flex: 2,
    },
    processName: {
        fontSize: theme.typography.fontSize.md,
        fontWeight: theme.typography.fontWeight.bold,
        color: theme.colors.textPrimary,
    },
    processPid: {
        fontSize: theme.typography.fontSize.sm,
        color: theme.colors.textSecondary,
    },
    processDetails: {
        flex: 1,
        alignItems: 'flex-end',
        marginRight: theme.spacing.md,
    },
    processStat: {
        fontSize: theme.typography.fontSize.xs,
        color: theme.colors.primaryLight,
    },
    killButton: {
        backgroundColor: theme.colors.danger,
        paddingHorizontal: theme.spacing.md,
        paddingVertical: theme.spacing.xs,
        borderRadius: theme.borderRadius.sm,
    },
    killButtonText: {
        color: '#fff',
        fontSize: theme.typography.fontSize.xs,
        fontWeight: 'bold',
    },
    loadingText: {
        marginTop: theme.spacing.md,
        color: theme.colors.textSecondary,
    },
    emptyContainer: {
        padding: theme.spacing.xl,
        alignItems: 'center',
    },
    emptyText: {
        color: theme.colors.textSecondary,
        textAlign: 'center',
    }
});
