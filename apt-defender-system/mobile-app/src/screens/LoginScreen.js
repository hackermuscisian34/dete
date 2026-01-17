/**
 * Login Screen
 */
import React, { useState } from 'react';
import {
    View,
    Text,
    TextInput,
    TouchableOpacity,
    StyleSheet,
    KeyboardAvoidingView,
    Platform,
    ActivityIndicator,
} from 'react-native';
import theme from '../theme/greenTheme';

export default function LoginScreen({ navigation }) {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [loading, setLoading] = useState(false);

    const handleLogin = async () => {
        setLoading(true);

        try {
            // TODO: Implement actual authentication
            // For now, just navigate to main app
            setTimeout(() => {
                navigation.replace('Main');
            }, 1000);
        } catch (error) {
            alert('Login failed. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <KeyboardAvoidingView
            style={styles.container}
            behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        >
            <View style={styles.content}>
                {/* Logo/Title */}
                <View style={styles.header}>
                    <Text style={styles.title}>APT Defender</Text>
                    <Text style={styles.subtitle}>Portable Security System</Text>
                </View>

                {/* Input Fields */}
                <View style={styles.form}>
                    <TextInput
                        style={styles.input}
                        placeholder="Email"
                        placeholderTextColor={theme.colors.textMuted}
                        value={email}
                        onChangeText={setEmail}
                        keyboardType="email-address"
                        autoCapitalize="none"
                        autoCorrect={false}
                    />

                    <TextInput
                        style={styles.input}
                        placeholder="Password"
                        placeholderTextColor={theme.colors.textMuted}
                        value={password}
                        onChangeText={setPassword}
                        secureTextEntry
                        autoCapitalize="none"
                    />

                    {/* Login Button */}
                    <TouchableOpacity
                        style={styles.loginButton}
                        onPress={handleLogin}
                        disabled={loading}
                    >
                        {loading ? (
                            <ActivityIndicator color={theme.colors.textOnPrimary} />
                        ) : (
                            <Text style={styles.loginButtonText}>Login</Text>
                        )}
                    </TouchableOpacity>

                    {/* Forgot Password */}
                    <TouchableOpacity style={styles.forgotPassword}>
                        <Text style={styles.forgotPasswordText}>Forgot Password?</Text>
                    </TouchableOpacity>
                </View>

                {/* Biometric Option (placeholder) */}
                <TouchableOpacity style={styles.biometricButton}>
                    <Text style={styles.biometricText}>Use Biometric Login</Text>
                </TouchableOpacity>
            </View>
        </KeyboardAvoidingView>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: theme.colors.background,
    },
    content: {
        flex: 1,
        justifyContent: 'center',
        padding: theme.spacing.xl,
    },
    header: {
        alignItems: 'center',
        marginBottom: theme.spacing.xxl,
    },
    title: {
        fontSize: theme.typography.fontSize.xxl,
        fontWeight: theme.typography.fontWeight.bold,
        color: theme.colors.primary,
        marginBottom: theme.spacing.sm,
    },
    subtitle: {
        fontSize: theme.typography.fontSize.md,
        color: theme.colors.textSecondary,
    },
    form: {
        marginBottom: theme.spacing.xl,
    },
    input: {
        backgroundColor: theme.colors.surface,
        borderRadius: theme.borderRadius.md,
        padding: theme.spacing.md,
        marginBottom: theme.spacing.md,
        fontSize: theme.typography.fontSize.md,
        color: theme.colors.textPrimary,
        borderWidth: 1,
        borderColor: theme.colors.primary,
    },
    loginButton: {
        backgroundColor: theme.colors.primary,
        borderRadius: theme.borderRadius.md,
        padding: theme.spacing.md,
        alignItems: 'center',
        marginTop: theme.spacing.md,
        ...theme.shadows.md,
    },
    loginButtonText: {
        color: theme.colors.textOnPrimary,
        fontSize: theme.typography.fontSize.lg,
        fontWeight: theme.typography.fontWeight.bold,
    },
    forgotPassword: {
        alignItems: 'center',
        marginTop: theme.spacing.md,
    },
    forgotPasswordText: {
        color: theme.colors.textSecondary,
        fontSize: theme.typography.fontSize.sm,
    },
    biometricButton: {
        alignItems: 'center',
        padding: theme.spacing.md,
    },
    biometricText: {
        color: theme.colors.primaryLight,
        fontSize: theme.typography.fontSize.md,
    },
});
