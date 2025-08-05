// constants/Theme.ts - Centralized theme constants for PrepSense
/**
 * Centralized theme colors and design tokens for the PrepSense app.
 * This ensures consistent design across all components.
 */

export const Theme = {
  colors: {
    // Primary Colors
    primary: '#FF6B6B',        // Coral red - main brand color
    primaryLight: '#FFE5E5',   // Light coral for backgrounds
    primaryDark: '#E55555',    // Darker coral for pressed states
    
    // Secondary Colors  
    secondary: '#6366F1',      // Indigo - for secondary actions
    secondaryLight: '#E0E7FF', // Light indigo for backgrounds
    secondaryDark: '#4F46E5',  // Darker indigo for pressed states
    
    // Semantic Colors
    success: '#4CAF50',        // Green for success states
    successLight: '#E8F5E9',   // Light green backgrounds
    warning: '#FF9800',        // Orange for warnings
    warningLight: '#FFF3E0',   // Light orange backgrounds
    error: '#F44336',          // Red for errors
    errorLight: '#FFEBEE',     // Light red backgrounds
    info: '#007AFF',           // Blue for info
    infoLight: '#E3F2FD',      // Light blue backgrounds
    
    // Neutral Colors
    text: '#1A1A1A',           // Primary text
    textSecondary: '#666666',  // Secondary text
    textLight: '#999999',      // Light text
    background: '#F8F9FA',     // Main background
    surface: '#FFFFFF',        // Card/surface background
    border: '#E0E0E0',         // Border color
    borderLight: '#F0F0F0',    // Light borders
    
    // Status Colors
    available: '#059669',      // Green for available items
    partial: '#F59E0B',        // Amber for partial availability
    missing: '#DC2626',        // Red for missing items
    
    // Interactive Colors
    link: '#007AFF',           // Links
    disabled: '#CCCCCC',       // Disabled elements
    shadow: 'rgba(0, 0, 0, 0.1)', // Shadows
  },
  
  // Spacing
  spacing: {
    xs: 4,
    sm: 8,
    md: 12,
    lg: 16,
    xl: 20,
    xxl: 24,
    xxxl: 32,
  },
  
  // Typography
  typography: {
    sizes: {
      xs: 12,
      sm: 14,
      md: 16,
      lg: 18,
      xl: 20,
      xxl: 24,
      xxxl: 32,
    },
    weights: {
      normal: '400',
      medium: '500',
      semiBold: '600',
      bold: '700',
    },
  },
  
  // Border Radius
  borderRadius: {
    sm: 4,
    md: 8,
    lg: 12,
    xl: 16,
    xxl: 24,
    round: 50,
  },
  
  // Shadows
  shadows: {
    sm: {
      shadowColor: '#000',
      shadowOffset: { width: 0, height: 1 },
      shadowOpacity: 0.05,
      shadowRadius: 2,
      elevation: 1,
    },
    md: {
      shadowColor: '#000',
      shadowOffset: { width: 0, height: 2 },
      shadowOpacity: 0.1,
      shadowRadius: 4,
      elevation: 3,
    },
    lg: {
      shadowColor: '#000',
      shadowOffset: { width: 0, height: 4 },
      shadowOpacity: 0.15,
      shadowRadius: 8,
      elevation: 5,
    },
  },
} as const;

// Convenient aliases for commonly used values
export const Colors = Theme.colors;
export const Spacing = Theme.spacing;
export const Typography = Theme.typography;
export const BorderRadius = Theme.borderRadius;
export const Shadows = Theme.shadows;