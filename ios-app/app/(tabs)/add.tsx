/**\n * This module is part of the PrepSense React Native app.\n * It defines a screen or component and interacts with context and API services.\n */
import React from 'react';
import { View, Text, StyleSheet } from 'react-native';

export default function AddScreen() {
  return (
    <View style={styles.container}>
      <Text style={styles.text}>Add Screen (Floating Action)</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: '#fff' },
  text: { fontSize: 24, color: '#297A56', fontWeight: 'bold' },
}); 