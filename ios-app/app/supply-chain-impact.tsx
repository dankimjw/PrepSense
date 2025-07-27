import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { Stack, useRouter } from 'expo-router';
import { SupplyChainImpactStats } from '../components/SupplyChainImpactStats';
import { CustomHeader } from './components/CustomHeader';

export default function SupplyChainImpactScreen() {
  const router = useRouter();

  return (
    <View style={styles.container}>
      <Stack.Screen
        options={{
          header: () => (
            <CustomHeader 
              title="Supply Chain Impact"
              showBackButton={true}
              onBackPress={() => router.back()}
            />
          )
        }}
      />
      
      <SupplyChainImpactStats userId="demo_user" />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f9fafb',
  },
});