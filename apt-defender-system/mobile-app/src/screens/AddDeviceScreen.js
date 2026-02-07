import React, { useState, useEffect } from 'react';
import {
    View,
    Text,
    StyleSheet,
    TouchableOpacity,
    ActivityIndicator,
    Alert,
    Share,
    TextInput,
    ScrollView
} from 'react-native';
import piClient from '../api/piClient';
import theme from '../theme/greenTheme';

export default function AddDeviceScreen({ navigation }) {
    const [pairingCode, setPairingCode] = useState(null);
    const [loading, setLoading] = useState(false);
    const [expiresIn, setExpiresIn] = useState(null);
    const [manualIp, setManualIp] = useState('');
    const [manualHostname, setManualHostname] = useState('');

    const generateNewCode = async () => {
        setLoading(true);
        try {
            const response = await piClient.generatePairingCode();
            if (response.success) {
                setPairingCode(response.data.pairing_token);
                setExpiresIn(response.data.expires_in_minutes);
            }
        } catch (error) {
            console.error('Error generating code:', error);
            Alert.alert('Error', 'Failed to generate pairing code. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    const handleShare = async () => {
        if (!pairingCode) return;
        try {
            await Share.share({
                message: `APT Defender Pairing Code: ${pairingCode}\nExpires in ${expiresIn} minutes.`,
            });
        } catch (error) {
            console.log(error.message);
        }
    };

    return (
        <ScrollView style={styles.container} contentContainerStyle={{ flexGrow: 1 }}>
            <View style={styles.content}>
                <Text style={styles.title}>Add New Device</Text>
                <Text style={styles.description}>
                    To protect your PC, you need to connect it to this Raspberry Pi agent.
                </Text>

                <View style={styles.stepContainer}>
                    <Text style={styles.stepNumber}>1</Text>
                    <Text style={styles.stepText}>Run the Helper Service on your PC.</Text>
                </View>

                <View style={styles.stepContainer}>
                    <Text style={styles.stepNumber}>2</Text>
                    <Text style={styles.stepText}>Generate a pairing code below.</Text>
                </View>

                <View style={styles.stepContainer}>
                    <Text style={styles.stepNumber}>3</Text>
                    <Text style={styles.stepText}>Enter the code and the Pi's IP address on your PC.</Text>
                </View>

                <View style={styles.codeContainer}>
                    {loading ? (
                        <ActivityIndicator size="large" color={theme.colors.primary} />
                    ) : pairingCode ? (
                        <>
                            <Text style={styles.codeLabel}>PAIRING CODE</Text>
                            <Text style={styles.codeText}>{pairingCode}</Text>
                            <Text style={styles.expiryText}>Expires in {expiresIn} minutes</Text>
                        </>
                    ) : (
                        <TouchableOpacity style={styles.generateButton} onPress={generateNewCode}>
                            <Text style={styles.generateButtonText}>Generate Code</Text>
                        </TouchableOpacity>
                    )}
                </View>

                {pairingCode && (
                    <TouchableOpacity style={styles.shareButton} onPress={handleShare}>
                        <Text style={styles.shareButtonText}>Share Code</Text>
                    </TouchableOpacity>
                )}

                <TouchableOpacity
                    style={styles.cancelButton}
                    onPress={() => navigation.goBack()}
                >
                    <Text style={styles.cancelButtonText}>Done</Text>
                </TouchableOpacity>

                <View style={styles.divider} />

                <View style={styles.manualSection}>
                    <Text style={styles.manualTitle}>Manual PC Discovery</Text>
                    <Text style={styles.manualSubtitle}>If your PC is not showing up, enter its details:</Text>

                    <TextInput
                        style={styles.input}
                        placeholder="PC IP Address (e.g. 192.168.1.5)"
                        placeholderTextColor={theme.colors.textSecondary}
                        value={manualIp}
                        onChangeText={setManualIp}
                    />
                    <TextInput
                        style={styles.input}
                        placeholder="PC Hostname (e.g. MY-LAPTOP)"
                        placeholderTextColor={theme.colors.textSecondary}
                        value={manualHostname}
                        onChangeText={setManualHostname}
                    />

                    <TouchableOpacity
                        style={styles.manualButton}
                        onPress={async () => {
                            if (!manualIp || !manualHostname) {
                                Alert.alert('Missing Info', 'Please enter both IP address and hostname');
                                return;
                            }

                            setLoading(true);
                            try {
                                const response = await piClient.registerDeviceManual(manualIp, manualHostname);
                                if (response.success) {
                                    Alert.alert(
                                        'Success',
                                        `PC "${response.data.hostname}" added successfully!`,
                                        [{ text: 'OK', onPress: () => navigation.navigate('Devices') }]
                                    );
                                }
                            } catch (error) {
                                console.error('Manual registration error:', error);
                                Alert.alert(
                                    'Connection Failed',
                                    'Could not connect to PC. Make sure:\n' +
                                    '1. Helper service is running on PC\n' +
                                    '2. IP address is correct\n' +
                                    '3. Both devices are on same network'
                                );
                            } finally {
                                setLoading(false);
                            }
                        }}
                    >
                        <Text style={styles.manualButtonText}>Add Manually</Text>
                    </TouchableOpacity>
                </View>
            </View>
        </ScrollView>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: theme.colors.background,
    },
    content: {
        padding: theme.spacing.xl,
        flex: 1,
    },
    title: {
        fontSize: 28,
        fontWeight: 'bold',
        color: theme.colors.textPrimary,
        marginTop: 20,
        marginBottom: theme.spacing.md,
        textAlign: 'center',
    },
    description: {
        fontSize: 16,
        color: theme.colors.textSecondary,
        textAlign: 'center',
        marginBottom: theme.spacing.xl,
    },
    stepContainer: {
        flexDirection: 'row',
        alignItems: 'center',
        marginBottom: theme.spacing.md,
        backgroundColor: theme.colors.surface,
        padding: theme.spacing.md,
        borderRadius: theme.borderRadius.md,
        borderWidth: 1,
        borderColor: theme.colors.primaryDark,
    },
    stepNumber: {
        width: 30,
        height: 30,
        borderRadius: 15,
        backgroundColor: theme.colors.primary,
        color: '#fff',
        textAlign: 'center',
        lineHeight: 30,
        fontWeight: 'bold',
        marginRight: theme.spacing.md,
    },
    stepText: {
        fontSize: 14,
        color: theme.colors.textPrimary,
        flex: 1,
    },
    codeContainer: {
        backgroundColor: theme.colors.surface,
        padding: theme.spacing.xl,
        borderRadius: theme.borderRadius.lg,
        alignItems: 'center',
        marginVertical: theme.spacing.xl,
        borderWidth: 2,
        borderColor: theme.colors.primary,
        borderStyle: 'dashed',
        minHeight: 150,
        justifyContent: 'center',
    },
    codeLabel: {
        fontSize: 12,
        color: theme.colors.primaryLight,
        fontWeight: 'bold',
        letterSpacing: 2,
        marginBottom: theme.spacing.sm,
    },
    codeText: {
        fontSize: 32,
        fontWeight: 'bold',
        color: theme.colors.textPrimary,
        letterSpacing: 4,
        textAlign: 'center',
    },
    expiryText: {
        fontSize: 12,
        color: theme.colors.textSecondary,
        marginTop: theme.spacing.sm,
    },
    generateButton: {
        backgroundColor: theme.colors.primary,
        paddingHorizontal: theme.spacing.xl,
        paddingVertical: theme.spacing.md,
        borderRadius: theme.borderRadius.md,
    },
    generateButtonText: {
        color: '#fff',
        fontSize: 18,
        fontWeight: 'bold',
    },
    shareButton: {
        backgroundColor: theme.colors.surface,
        padding: theme.spacing.md,
        borderRadius: theme.borderRadius.md,
        alignItems: 'center',
        marginBottom: theme.spacing.md,
        borderWidth: 1,
        borderColor: theme.colors.primary,
    },
    shareButtonText: {
        color: theme.colors.primary,
        fontSize: 16,
        fontWeight: 'bold',
    },
    cancelButton: {
        padding: theme.spacing.md,
        alignItems: 'center',
    },
    cancelButtonText: {
        color: theme.colors.textSecondary,
        fontSize: 16,
    },
    divider: {
        height: 1,
        backgroundColor: theme.colors.primaryDark,
        marginVertical: theme.spacing.xl,
    },
    manualSection: {
        marginBottom: 40,
    },
    manualTitle: {
        fontSize: 18,
        fontWeight: 'bold',
        color: theme.colors.textPrimary,
        marginBottom: 4,
    },
    manualSubtitle: {
        fontSize: 14,
        color: theme.colors.textSecondary,
        marginBottom: theme.spacing.md,
    },
    input: {
        backgroundColor: theme.colors.surface,
        color: theme.colors.textPrimary,
        padding: theme.spacing.md,
        borderRadius: theme.borderRadius.md,
        marginBottom: theme.spacing.sm,
        borderWidth: 1,
        borderColor: theme.colors.primaryDark,
    },
    manualButton: {
        backgroundColor: theme.colors.primaryDark,
        padding: theme.spacing.md,
        borderRadius: theme.borderRadius.md,
        alignItems: 'center',
        marginTop: theme.spacing.sm,
    },
    manualButtonText: {
        color: theme.colors.primaryLight,
        fontWeight: 'bold',
    }
});
