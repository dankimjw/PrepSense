// app/add-item.tsx - Part of the PrepSense mobile app
import React, { useEffect } from 'react';
import { View, StyleSheet } from 'react-native';
import { useRouter } from 'expo-router';
import { AddItemModalV2 } from '../components/modals/AddItemModalV2';

export default function AddItemScreen() {
  const router = useRouter();

  const handleClose = () => {
    router.back();
  };

  const handleSuccess = () => {
    // Navigate back to home after successful addition
    router.replace('/(tabs)');
  };

  // Since this is a screen that shows a modal, we want the modal to be visible
  return (
    <View style={styles.container}>
      <AddItemModalV2
        visible={true}
        onClose={handleClose}
        onSuccess={handleSuccess}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: 'transparent',
  },
});