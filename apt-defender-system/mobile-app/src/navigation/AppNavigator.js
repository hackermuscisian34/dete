import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { StatusBar } from 'expo-status-bar';

import LoginScreen from '../screens/LoginScreen';
import SignupScreen from '../screens/SignupScreen';
import DevicesScreen from '../screens/DevicesScreen';
import DeviceDetailScreen from '../screens/DeviceDetailScreen';
import DeviceProcessesScreen from '../screens/DeviceProcessesScreen';
import DeviceConnectionsScreen from '../screens/DeviceConnectionsScreen';
import DeviceTimelineScreen from '../screens/DeviceTimelineScreen';
import DeviceTelemetryScreen from '../screens/DeviceTelemetryScreen';
import AddDeviceScreen from '../screens/AddDeviceScreen';

const Stack = createNativeStackNavigator();

const AppNavigator = () => {
    return (
        <NavigationContainer>
            <StatusBar style="light" />
            <Stack.Navigator
                initialRouteName="Login"
                screenOptions={{
                    headerStyle: {
                        backgroundColor: '#1B5E20', // Dark green background
                    },
                    headerTintColor: '#E8F5E9', // Light text
                    headerTitleStyle: {
                        fontWeight: 'bold',
                    },
                    contentStyle: {
                        backgroundColor: '#000000', // Default background
                    }
                }}
            >
                <Stack.Screen
                    name="Login"
                    component={LoginScreen}
                    options={{ headerShown: false }}
                />
                <Stack.Screen
                    name="Signup"
                    component={SignupScreen}
                    options={{ headerShown: false }}
                />
                <Stack.Screen
                    name="Devices"
                    component={DevicesScreen}
                    options={{ title: 'My Devices' }}
                />
                <Stack.Screen
                    name="DeviceDetail"
                    component={DeviceDetailScreen}
                    options={({ route }) => ({ title: route.params?.deviceName || 'Device Details' })}
                />
                <Stack.Screen
                    name="DeviceProcesses"
                    component={DeviceProcessesScreen}
                    options={{ title: 'Running Programs' }}
                />
                <Stack.Screen
                    name="DeviceConnections"
                    component={DeviceConnectionsScreen}
                    options={{ title: 'Network' }}
                />
                <Stack.Screen
                    name="DeviceTimeline"
                    component={DeviceTimelineScreen}
                    options={{ title: 'Timeline' }}
                />
                <Stack.Screen
                    name="DeviceTelemetry"
                    component={DeviceTelemetryScreen}
                    options={{ title: 'System Telemetry' }}
                />
                <Stack.Screen
                    name="AddDevice"
                    component={AddDeviceScreen}
                    options={{ title: 'Add Device' }}
                />
            </Stack.Navigator>
        </NavigationContainer>
    );
};

export default AppNavigator;
