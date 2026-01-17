/**
 * Green Color Theme for APT Defender
 */

export const colors = {
  // Primary colors
  primary: '#00C853',        // Material Green A700
  primaryLight: '#69F0AE',   // Light green accent
  primaryDark: '#1B5E20',    // Dark green
  
  // Surface colors
  background: '#1B5E20',     // Dark green background
  surface: '#2E7D32',        // Surface elements
  surfaceLight: '#388E3C',   // Lighter surface
  
  // Status colors
  success: '#4CAF50',        // Success green
  warning: '#FFC107',        // Warning amber
  danger: '#F44336',         // Danger red
  info: '#2196F3',           // Info blue
  
  // Text colors
  textPrimary: '#E8F5E9',    // Light green text
  textSecondary: '#C8E6C9',  // Secondary text
  textMuted: '#A5D6A7',      // Muted text
  textOnPrimary: '#FFFFFF',  // White text on primary
  
  // Threat severity colors
  threatCritical: '#D32F2F',  // Dark red
  threatHigh: '#F44336',      // Red
  threatMedium: '#FF9800',     // Orange
  threatLow: '#FFC107',        // Amber
  threatInfo: '#2196F3',       // Blue
  
  // Other
  transparent: 'transparent',
  overlay: 'rgba(0, 0, 0, 0.5)',
  divider: '#4CAF50',
};

export const spacing = {
  xs: 4,
  sm: 8,
  md: 16,
  lg: 24,
  xl: 32,
  xxl: 48,
};

export const typography = {
  fontFamily: {
    regular: 'System',
    medium: 'System',
    bold: 'System',
  },
  fontSize: {
    xs: 12,
    sm: 14,
    md: 16,
    lg: 18,
    xl: 24,
    xxl: 32,
  },
  fontWeight: {
    normal: '400',
    medium: '500',
    bold: '700',
  },
};

export const borderRadius = {
  sm: 4,
  md: 8,
  lg: 16,
  xl: 24,
  full: 9999,
};

export const shadows = {
  sm: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 2,
  },
  md: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.15,
    shadowRadius: 8,
    elevation: 4,
  },
  lg: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.2,
    shadowRadius: 16,
    elevation: 8,
  },
};

export default {
  colors,
  spacing,
  typography,
  borderRadius,
  shadows,
};
