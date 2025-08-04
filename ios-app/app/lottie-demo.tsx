import React from 'react';
import { View, Text, ScrollView, StyleSheet } from 'react-native';
import { Stack } from 'expo-router';
import { Button } from 'react-native-paper';
import {
  HybridLottie,
  SuccessAnimation,
  LoadingAnimation,
  EmptyStateAnimation,
  ErrorAnimation,
  ScanningAnimation,
  useLottieAnimation,
} from '../components/hybrid/HybridLottie';

export default function LottieDemoScreen() {
  const [showImproved, setShowImproved] = React.useState(true);
  
  // Animation hooks for controlled animations
  const successAnim = useLottieAnimation(true, 3000);
  const errorAnim = useLottieAnimation(true, 3000);
  
  return (
    <>
      <Stack.Screen 
        options={{ 
          title: 'Lottie Animations Demo',
          headerBackTitle: 'Back',
        }} 
      />
      <ScrollView style={styles.container} showsVerticalScrollIndicator={false}>
        <Text style={styles.header}>PrepSense Lottie Animations</Text>
        <Text style={styles.subtitle}>Smooth, modern animations for a delightful user experience</Text>
        
        {/* Animation Quality Notice */}
        <View style={styles.noticeContainer}>
          <Text style={styles.noticeText}>
            💡 For production, download high-quality animations from LottieFiles.com
          </Text>
        </View>
        
        {/* Success Animation */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Success Animation</Text>
          <Text style={styles.sectionDescription}>Shows when items are added successfully</Text>
          <SuccessAnimation 
            ref={successAnim.ref}
            onAnimationFinish={successAnim.onAnimationFinish}
          />
          <Button 
            mode="contained"
            onPress={successAnim.play}
            disabled={successAnim.isPlaying}
            style={styles.button}
          >
            Play Success
          </Button>
        </View>
        
        {/* Loading Animation */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Loading Animation</Text>
          <Text style={styles.sectionDescription}>Used in search bars and loading states</Text>
          <LoadingAnimation />
        </View>
        
        {/* Scanning Animation */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Scanning Animation</Text>
          <Text style={styles.sectionDescription}>For receipt and barcode scanning</Text>
          <ScanningAnimation />
        </View>
        
        {/* Empty State */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Empty State Animation</Text>
          <Text style={styles.sectionDescription}>When pantry or lists are empty</Text>
          <EmptyStateAnimation />
        </View>
        
        {/* Error Animation */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Error Animation</Text>
          <Text style={styles.sectionDescription}>For error states and failures</Text>
          <ErrorAnimation 
            ref={errorAnim.ref}
            onAnimationFinish={errorAnim.onAnimationFinish}
          />
          <Button 
            mode="outlined"
            onPress={errorAnim.play}
            disabled={errorAnim.isPlaying}
            style={styles.button}
            textColor="#EF4444"
          >
            Play Error
          </Button>
        </View>
        
        {/* Custom Colors Example */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Custom Themed Animation</Text>
          <Text style={styles.sectionDescription}>Success animation with custom colors</Text>
          <HybridLottie
            source={require('../assets/lottie/success-check.json')}
            size={120}
            loop={false}
            colorFilters={[
              {
                keypath: "**",
                color: "#DB2777", // Pink color
              }
            ]}
          />
        </View>
        
        {/* Small Inline Loading */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Inline Loading States</Text>
          <View style={styles.inlineExample}>
            <Text style={styles.inlineText}>Searching pantry items</Text>
            <LoadingAnimation size={24} />
          </View>
        </View>
      </ScrollView>
    </>
  );
}

const styles = StyleSheet.create({
  toggleContainer: {
    flexDirection: 'row',
    justifyContent: 'center',
    gap: 12,
    marginBottom: 16,
    paddingHorizontal: 16,
  },
  toggleButton: {
    flex: 1,
  },
  animationContainer: {
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: 160,
  },
  container: {
    flex: 1,
    backgroundColor: '#F9FAFB',
  },
  header: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#111827',
    textAlign: 'center',
    marginTop: 20,
  },
  subtitle: {
    fontSize: 16,
    color: '#6B7280',
    textAlign: 'center',
    marginTop: 8,
    marginBottom: 24,
    paddingHorizontal: 20,
  },
  section: {
    backgroundColor: 'white',
    marginHorizontal: 16,
    marginVertical: 8,
    padding: 20,
    borderRadius: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 2,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: '#111827',
    marginBottom: 4,
  },
  sectionDescription: {
    fontSize: 14,
    color: '#6B7280',
    marginBottom: 16,
  },
  button: {
    marginTop: 16,
  },
  inlineExample: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#F3F4F6',
    padding: 12,
    borderRadius: 8,
  },
  inlineText: {
    flex: 1,
    fontSize: 16,
    color: '#374151',
  },
  noticeContainer: {
    backgroundColor: '#FEF3C7',
    marginHorizontal: 16,
    marginBottom: 16,
    padding: 12,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#FCD34D',
  },
  noticeText: {
    fontSize: 14,
    color: '#92400E',
    textAlign: 'center',
  },
});