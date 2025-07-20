import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Alert,
  ScrollView,
  ActivityIndicator,
  Image,
} from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons, MaterialIcons } from '@expo/vector-icons';
import * as ImagePicker from 'expo-image-picker';
import { Config } from '../config';
import { LinearGradient } from 'expo-linear-gradient';
import { Buffer } from 'buffer';


export default function ReceiptScannerScreen() {
  const router = useRouter();
  const [image, setImage] = useState<string | null>(null);
  const [isScanning, setIsScanning] = useState(false);

  useEffect(() => {
    requestPermissions();
  }, []);

  const requestPermissions = async () => {
    const { status: cameraStatus } = await ImagePicker.requestCameraPermissionsAsync();
    const { status: libraryStatus } = await ImagePicker.requestMediaLibraryPermissionsAsync();
    
    if (cameraStatus !== 'granted' || libraryStatus !== 'granted') {
      Alert.alert(
        'Permissions Required',
        'Camera and photo library permissions are required to scan receipts.',
        [{ text: 'OK' }]
      );
    }
  };

  const pickImage = async (source: 'camera' | 'library') => {
    let result;
    
    if (source === 'camera') {
      result = await ImagePicker.launchCameraAsync({
        mediaTypes: ImagePicker.MediaTypeOptions.Images,
        allowsEditing: true,
        quality: 0.8,
        base64: true,
      });
    } else {
      result = await ImagePicker.launchImageLibraryAsync({
        mediaTypes: ImagePicker.MediaTypeOptions.Images,
        allowsEditing: true,
        quality: 0.8,
        base64: true,
      });
    }

    if (!result.canceled && result.assets[0]) {
      setImage(result.assets[0].uri);
      if (result.assets[0].base64) {
        scanReceipt(result.assets[0].base64);
      }
    }
  };

  const scanReceipt = async (base64Image: string) => {
    setIsScanning(true);
    
    try {
      const response = await fetch(`${Config.API_BASE_URL}/ocr/scan-receipt`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          image_base64: base64Image,
          user_id: 111,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to scan receipt');
      }

      const data = await response.json();
      
      if (data.success && data.items.length > 0) {
        // Transform OCR items to match upload-photo item format
        const transformedItems = data.items.map((item: any) => ({
          item_name: item.name,
          quantity_amount: item.quantity || 1,
          quantity_unit: item.unit || 'each',
          expected_expiration: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0], // Default 7 days
          category: item.category || 'Uncategorized',
          count: 1,
          price: item.price
        }));

        // Navigate to items-detected screen for full editing experience
        const dataParam = Buffer.from(JSON.stringify(transformedItems)).toString('base64');
        
        router.replace({
          pathname: '/items-detected',
          params: { 
            data: dataParam,
            photoUri: image,
            source: 'receipt-scanner'
          },
        });
        return;
      } else {
        Alert.alert(
          'No Items Found',
          'Could not extract any items from the receipt. Try taking a clearer photo.',
          [{ text: 'OK' }]
        );
      }
    } catch (error) {
      console.error('Error scanning receipt:', error);
      Alert.alert(
        'Scan Failed',
        'Failed to scan receipt. Please try again with a clearer image.',
        [{ text: 'OK' }]
      );
    } finally {
      setIsScanning(false);
    }
  };




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
        {!image ? (
          // Image selection view
          <View style={styles.scanContainer}>
            <LinearGradient
              colors={['#297A56', '#1F5A40']}
              style={styles.iconContainer}
            >
              <MaterialIcons name="receipt-long" size={80} color="#fff" />
            </LinearGradient>
            
            <Text style={styles.title}>Scan Your Receipt</Text>
            <Text style={styles.subtitle}>
              Take a photo or select from gallery to automatically add items to your pantry
            </Text>

            <View style={styles.buttonContainer}>
              <TouchableOpacity
                style={styles.primaryButton}
                onPress={() => pickImage('camera')}
              >
                <Ionicons name="camera" size={24} color="#fff" />
                <Text style={styles.primaryButtonText}>Take Photo</Text>
              </TouchableOpacity>

              <TouchableOpacity
                style={styles.secondaryButton}
                onPress={() => pickImage('library')}
              >
                <Ionicons name="images" size={24} color="#297A56" />
                <Text style={styles.secondaryButtonText}>Choose from Gallery</Text>
              </TouchableOpacity>
            </View>

            <View style={styles.tipsContainer}>
              <Text style={styles.tipsTitle}>Tips for best results:</Text>
              <Text style={styles.tipText}>• Ensure good lighting and minimal shadows</Text>
              <Text style={styles.tipText}>• Keep receipt flat and fully visible</Text>
              <Text style={styles.tipText}>• Avoid blurry or angled photos</Text>
            </View>
          </View>
        ) : (
          // Results view
          <View style={styles.resultsContainer}>
            <View style={styles.imagePreview}>
              <Image source={{ uri: image }} style={styles.receiptImage} />
              {isScanning && (
                <View style={styles.scanningOverlay}>
                  <ActivityIndicator size="large" color="#fff" />
                  <Text style={styles.scanningText}>Scanning receipt...</Text>
                </View>
              )}
            </View>

          </View>
        )}
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
  resultsContainer: {
    padding: 16,
  },
  imagePreview: {
    position: 'relative',
    marginBottom: 20,
    borderRadius: 12,
    overflow: 'hidden',
  },
  receiptImage: {
    width: '100%',
    height: 300,
    resizeMode: 'contain',
    backgroundColor: '#f0f0f0',
  },
  scanningOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0,0,0,0.7)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  scanningText: {
    color: '#fff',
    fontSize: 16,
    marginTop: 12,
  },
});