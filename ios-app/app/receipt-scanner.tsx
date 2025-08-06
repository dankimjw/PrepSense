import React, { useEffect, useState, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Alert,
  ScrollView,
} from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons, MaterialIcons } from '@expo/vector-icons';
import * as ImagePicker from 'expo-image-picker';
import { LinearGradient } from 'expo-linear-gradient';
import { imageDataStore } from '../utils/imageDataStore';

export default function ReceiptScannerScreen() {
  const router = useRouter();
  const [isProcessing, setIsProcessing] = useState(false);
  const lastPressRef = useRef(0);

  useEffect(() => {
    requestPermissions();
  }, []);

  const requestPermissions = async () => {
    const { status } = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (status !== 'granted') {
      Alert.alert(
        'Permissions Required',
        'Photo library permissions are required to scan receipts.',
        [{ text: 'OK' }]
      );
    }
  };

  const pickImage = async () => {
    // Reduced debounce: prevent multiple calls within 300ms (more responsive)
    const now = Date.now();
    if (now - lastPressRef.current < 300) {
      console.log('Button press ignored - too soon after last press');
      return;
    }
    lastPressRef.current = now;

    if (isProcessing) {
      console.log('Already processing image selection');
      return;
    }

    console.log('Starting receipt image selection process...');
    setIsProcessing(true);

    try {
      const result = await ImagePicker.launchImageLibraryAsync({
        mediaTypes: ['images'],
        allowsEditing: true,
        quality: 0.8,
        base64: true,
      });

      if (!result.canceled && result.assets && result.assets[0]) {
        const imageUri = result.assets[0].uri;
        const base64Image = result.assets[0].base64;

        if (!base64Image) {
          Alert.alert('Error', 'Failed to process image');
          setIsProcessing(false);
          return;
        }

        // Store image data in memory store
        const imageKey = `receipt_${Date.now()}`;
        imageDataStore.storeImageData(imageKey, base64Image);

        // Navigate immediately with just the key reference
        console.log(
          'Receipt image selected, navigating to loading-facts immediately...'
        );
        console.log('Base64 length:', base64Image.length);

        router.replace({
          pathname: '/loading-facts',
          params: {
            photoUri: imageUri,
            scanMode: 'receipt',
            imageKey: imageKey, // Pass key instead of data
          },
        });
      } else {
        console.log('Receipt image selection cancelled by user');
        setIsProcessing(false);
      }
    } catch (error) {
      console.error('Error picking image:', error);
      Alert.alert('Error', 'Failed to select image');
      setIsProcessing(false);
    } finally {
      // Ensure processing state is always reset after a delay
      setTimeout(() => {
        setIsProcessing(false);
      }, 100);
    }
  };

  // Removed scanReceipt - navigation happens immediately in pickImage

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity
          style={styles.backButton}
          onPress={() => router.back()}
        >
          <Ionicons name="arrow-back" size={24} color="#333" />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Receipt Scanner</Text>
        <View style={{ width: 40 }} />
      </View>

      <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
        {/* Image selection view - always shown since we navigate immediately */}
        <View style={styles.scanContainer}>
          <LinearGradient
            colors={['#297A56', '#1F5A40']}
            style={styles.iconContainer}
          >
            <MaterialIcons name="receipt-long" size={80} color="#fff" />
          </LinearGradient>

          <Text style={styles.title}>Scan Your Receipt</Text>
          <Text style={styles.subtitle}>
            Take a photo or select from gallery to automatically add items to
            your pantry
          </Text>

          <View style={styles.buttonContainer}>
            <TouchableOpacity
              style={[
                styles.primaryButton,
                isProcessing && styles.buttonDisabled,
              ]}
              onPress={pickImage}
              disabled={isProcessing}
              activeOpacity={0.8}
              delayPressIn={0}
              delayPressOut={0}
            >
              <Ionicons name="camera" size={24} color="#fff" />
              <Text style={styles.primaryButtonText}>
                {isProcessing ? 'Processing...' : 'Take Photo'}
              </Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={[
                styles.secondaryButton,
                isProcessing && styles.buttonDisabled,
              ]}
              onPress={pickImage}
              disabled={isProcessing}
              activeOpacity={0.8}
              delayPressIn={0}
              delayPressOut={0}
            >
              <Ionicons name="images" size={24} color="#297A56" />
              <Text style={styles.secondaryButtonText}>
                {isProcessing ? 'Processing...' : 'Choose from Gallery'}
              </Text>
            </TouchableOpacity>
          </View>

          <View style={styles.tipsContainer}>
            <Text style={styles.tipsTitle}>Tips for best results:</Text>
            <Text style={styles.tipText}>
              • Ensure good lighting and minimal shadows
            </Text>
            <Text style={styles.tipText}>
              • Keep receipt flat and fully visible
            </Text>
            <Text style={styles.tipText}>• Avoid blurry or angled photos</Text>
          </View>
        </View>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingTop: 50,
    paddingBottom: 16,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  backButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#f0f0f0',
    justifyContent: 'center',
    alignItems: 'center',
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#333',
  },
  content: {
    flex: 1,
  },
  scanContainer: {
    alignItems: 'center',
    padding: 32,
  },
  iconContainer: {
    width: 160,
    height: 160,
    borderRadius: 80,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 32,
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 12,
  },
  subtitle: {
    fontSize: 16,
    color: '#666',
    textAlign: 'center',
    marginBottom: 32,
    paddingHorizontal: 20,
    lineHeight: 22,
  },
  buttonContainer: {
    width: '100%',
    gap: 16,
  },
  primaryButton: {
    flexDirection: 'row',
    backgroundColor: '#297A56',
    paddingVertical: 16,
    paddingHorizontal: 24,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
  },
  primaryButtonText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: '600',
  },
  secondaryButton: {
    flexDirection: 'row',
    backgroundColor: '#fff',
    paddingVertical: 16,
    paddingHorizontal: 24,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    borderWidth: 2,
    borderColor: '#297A56',
  },
  secondaryButtonText: {
    color: '#297A56',
    fontSize: 18,
    fontWeight: '600',
  },
  tipsContainer: {
    marginTop: 48,
    padding: 20,
    backgroundColor: '#f0f7f4',
    borderRadius: 12,
    width: '100%',
  },
  tipsTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#297A56',
    marginBottom: 12,
  },
  tipText: {
    fontSize: 14,
    color: '#666',
    marginBottom: 6,
  },
  buttonDisabled: {
    opacity: 0.6,
  },
});
