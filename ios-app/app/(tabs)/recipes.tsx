// app/(tabs)/recipes.tsx - Part of the PrepSense mobile app
import React from 'react';
import { View, Text, StyleSheet } from 'react-native';

export default function RecipesScreen() {
  return (
    <View style={styles.container}>
      <Text style={styles.text}>Recipes Screen</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: '#fff' },
  text: { fontSize: 24, color: '#297A56', fontWeight: 'bold' },
}); 