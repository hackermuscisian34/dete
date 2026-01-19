import React, { useState, useEffect } from 'react';
import {
    View,
    Text,
    FlatList,
    StyleSheet,
    ActivityIndicator,
    RefreshControl
} from 'react-native';
import piClient from '../api/piClient';
import theme from '../theme/greenTheme';

export default function DeviceTimelineScreen({ route, navigation }) {
    const { deviceId } = route.params;
    const [events, setEvents] = useState([]);
    const [loading, setLoading] = useState(true);
    const [refreshing, setRefreshing] = useState(false);

    useEffect(() => {
        loadTimeline();
    }, [deviceId]);

    const loadTimeline = async () => {
        try {
            const response = await piClient.getDeviceTimeline(deviceId);
            if (response.success) {
                setEvents(response.data.events || []);
            }
        } catch (error) {
            console.error('Error loading timeline:', error);
        } finally {
            setLoading(false);
            setRefreshing(false);
        }
    };

    const formatDate = (dateStr) => {
        const d = new Date(dateStr);
        return d.toLocaleTimeString() + ' ' + d.toLocaleDateString();
    };

    const renderEventItem = ({ item }) => (
        <View style={styles.eventItem}>
            <View style={[styles.severityBar, { backgroundColor: item.severity > 7 ? theme.colors.danger : theme.colors.primary }]} />
            <View style={styles.eventContent}>
                <View style={styles.eventHeader}>
                    <Text style={styles.eventType}>{item.event_type.replace('_', ' ').toUpperCase()}</Text>
                    <Text style={styles.eventTime}>{formatDate(item.timestamp)}</Text>
                </View>
                <Text style={styles.eventDetails}>{item.details}</Text>
                <Text style={styles.eventSource}>Source: {item.source}</Text>
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
                <Text style={styles.title}>Security Timeline</Text>
                <Text style={styles.subtitle}>Recent events from this device</Text>
            </View>

            <FlatList
                data={events}
                keyExtractor={(item) => item.id.toString()}
                renderItem={renderEventItem}
                contentContainerStyle={styles.listContent}
                refreshControl={
                    <RefreshControl
                        refreshing={refreshing}
                        onRefresh={() => {
                            setRefreshing(true);
                            loadTimeline();
                        }}
                        tintColor={theme.colors.primary}
                    />
                }
                ListEmptyComponent={
                    <View style={styles.emptyContainer}>
                        <Text style={styles.emptyText}>No forensic events found</Text>
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
    eventItem: {
        flexDirection: 'row',
        backgroundColor: theme.colors.surface,
        borderRadius: theme.borderRadius.md,
        marginBottom: theme.spacing.sm,
        overflow: 'hidden',
        borderWidth: 1,
        borderColor: theme.colors.primaryDark,
    },
    severityBar: {
        width: 6,
    },
    eventContent: {
        flex: 1,
        padding: theme.spacing.md,
    },
    eventHeader: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        marginBottom: 4,
    },
    eventType: {
        fontSize: 10,
        fontWeight: 'bold',
        color: theme.colors.primaryLight,
    },
    eventTime: {
        fontSize: 10,
        color: theme.colors.textSecondary,
    },
    eventDetails: {
        fontSize: theme.typography.fontSize.sm,
        color: theme.colors.textPrimary,
        marginBottom: 4,
    },
    eventSource: {
        fontSize: 9,
        color: theme.colors.textSecondary,
        fontStyle: 'italic',
    },
    emptyContainer: {
        padding: theme.spacing.xl,
        alignItems: 'center',
    },
    emptyText: {
        color: theme.colors.textSecondary,
    }
});
