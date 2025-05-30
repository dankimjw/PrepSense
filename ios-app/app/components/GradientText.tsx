// app/components/GradientText.tsx - Gradient text component for PrepSense branding
import React from 'react';
import { Text, StyleSheet, TextStyle } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import MaskedView from '@react-native-masked-view/masked-view';

interface GradientTextProps {
  children: string;
  style?: TextStyle;
  colors?: string[];
}

export default function GradientText({ 
  children, 
  style,
  colors = ['#4ECDC4', '#7FE19E'] // Default to PrepSense logo gradient colors
}: GradientTextProps) {
  return (
    <MaskedView
      style={style}
      maskElement={
        <Text style={[styles.text, style]}>
          {children}
        </Text>
      }
    >
      <LinearGradient
        colors={colors}
        start={{ x: 0, y: 0 }}
        end={{ x: 1, y: 0 }}
        style={[StyleSheet.absoluteFillObject, style]}
      />
    </MaskedView>
  );
}

const styles = StyleSheet.create({
  text: {
    backgroundColor: 'transparent',
  },
});