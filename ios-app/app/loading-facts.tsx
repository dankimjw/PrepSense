// app/loading-facts.tsx - Part of the PrepSense mobile app
import React, { useEffect, useRef, useState } from 'react';
import { View, Text, StyleSheet, ActivityIndicator, Alert } from 'react-native';
import { useRouter, useLocalSearchParams, Stack } from 'expo-router';
import foodFacts from './utils/facts';
import { CustomHeader } from './components/CustomHeader';
import * as FileSystem from 'expo-file-system';
import { Buffer } from 'buffer';
import { Config } from '../config';
import { imageDataStore } from '../utils/imageDataStore';

const UPLOAD_URL = `${Config.API_BASE_URL}/images/upload`;

export default function LoadingFactsScreen() {
  const [factIndex, setFactIndex] = useState(() => Math.floor(Math.random() * foodFacts.length));
  const [loading, setLoading] = useState(true);
  const intervalRef = useRef<any>(null);
  const router = useRouter();
  const { photoUri, scanMode, imageData, imageKey } = useLocalSearchParams<{ 
    photoUri: string;
    scanMode?: string;
    imageData?: string;
    imageKey?: string;
  }>();

  console.log('LoadingFactsScreen rendered with params:', { photoUri, scanMode, imageKey, hasImageData: !!imageData });

  useEffect(() => {
    intervalRef.current = setInterval(() => {
      setFactIndex((prev) => (prev + 1) % foodFacts.length);
    }, 4000);
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, []);

  useEffect(() => {
    const processImage = async () => {
      try {
        if (!photoUri) throw new Error('No photo URI provided');
        
        if (scanMode === 'items') {
          // Handle OCR scanning flow
          console.log('Processing OCR scan...');
          
          // Get image data from store or params
          let base64Data = imageData;
          if (imageKey && !base64Data) {
            base64Data = imageDataStore.getImageData(imageKey);
          }
          
          if (!base64Data) {
            throw new Error('No image data available');
          }
          
          try {
            const response = await fetch(`${Config.API_BASE_URL}/ocr/scan-items`, {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
              },
              body: JSON.stringify({
                image_base64: base64Data
              }),
            });

            if (!response.ok) {
              throw new Error('Failed to scan item');
            }

            const data = await response.json();
            
            if (data.success && data.items.length > 0) {
              // Transform scanned items to match the expected format
              const transformedItems = data.items.map((item: any) => ({
                item_name: item.name || item.product_name,
                quantity_amount: item.quantity || 1,
                quantity_unit: item.unit || 'each',
                expected_expiration: item.expiration_date || 
                  new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0], // Default 7 days
                category: item.category || 'Uncategorized',
                barcode: item.barcode,
                brand: item.brand,
                nutrition_info: item.nutrition_info
              }));

              // Navigate to items-detected screen
              const dataParam = Buffer.from(JSON.stringify(transformedItems)).toString('base64');
              
              router.replace({
                pathname: '/items-detected',
                params: { 
                  data: dataParam,
                  photoUri: photoUri,
                  source: 'scan-items'
                },
              });
              return;
            } else {
              Alert.alert(
                'No Items Found',
                'Could not identify the item. Try taking a clearer photo of the product label or barcode.',
                [{ text: 'OK' }]
              );
              router.replace('/scan-items');
              return;
            }
          } catch (error) {
            console.error('Error scanning item:', error);
            Alert.alert(
              'Scan Failed',
              'Failed to scan item. Please try again with a clearer image.',
              [{ text: 'OK' }]
            );
            router.replace('/scan-items');
            return;
          }
        } else if (scanMode === 'receipt') {
          // Handle receipt scanning flow
          console.log('Processing receipt scan...');
          
          // Get image data from store or params
          let base64Data = imageData;
          if (imageKey && !base64Data) {
            base64Data = imageDataStore.getImageData(imageKey);
          }
          
          if (!base64Data) {
            throw new Error('No image data available');
          }
          
          try {
            const response = await fetch(`${Config.API_BASE_URL}/ocr/scan-receipt`, {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
              },
              body: JSON.stringify({
                image_base64: base64Data,
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
                  photoUri: photoUri,
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
              router.replace('/receipt-scanner');
              return;
            }
          } catch (error) {
            console.error('Error scanning receipt:', error);
            Alert.alert(
              'Scan Failed',
              'Failed to scan receipt. Please try again with a clearer image.',
              [{ text: 'OK' }]
            );
            router.replace('/receipt-scanner');
            return;
          }
        } else {
          // Handle original receipt upload flow
          console.log('Photo URI:', photoUri);
          const info = await FileSystem.getInfoAsync(photoUri);
          console.log('File info:', info);
          const body = new FormData();
          const fileExtension = info.uri.split('.').pop()?.toLowerCase() ?? 'jpg';
          const mimeType = fileExtension === 'png' ? 'image/png' : 'image/jpeg';
          const fileData = {
            uri: photoUri,
            name: info.uri.split('/').pop() ?? 'image.jpg',
            type: mimeType,
          };
          body.append('file', fileData as any);
          console.log('File data being sent:', {
            uri: fileData.uri,
            name: fileData.name,
            type: fileData.type,
            ...(info.exists ? {
              size: info.size,
              md5: info.md5
            } : {})
          });

          console.log('Making request to:', UPLOAD_URL);
          try {
            const r = await fetch(UPLOAD_URL, { 
              method: 'POST', 
              body,
              headers: {
                'Accept': 'application/json',
              }
            });
            console.log('Response status:', r.status);
            if (!r.ok) {
              const errorText = await r.text();
              console.error('Error response:', errorText);
              throw new Error(`HTTP ${r.status}: ${errorText}`);
            }

            const responseData = await r.json();
            console.log('Response data:', responseData);
            const { pantry_items } = responseData;
            if (!Array.isArray(pantry_items) || pantry_items.length === 0) {
              Alert.alert('No items detected', 'Try another photo?');
              router.replace('/');
              return;
            }
            
            // Add default category to items if not present
            const itemsWithCategory = pantry_items.map((item: any) => ({
              ...item,
              category: item.category || 'Uncategorized'
            }));

            const dataParam = Buffer
              .from(JSON.stringify(itemsWithCategory))
              .toString('base64');

            router.replace({
              pathname: '/items-detected',
              params: { data: dataParam, photoUri },
            });
          } catch (e: any) {
            console.error('Upload error:', e);
            if (e.name === 'TypeError' && e.message.includes('Network request failed')) {
              Alert.alert('Connection Error', 'Could not connect to the server. Please check if the server is running at ' + UPLOAD_URL);
            } else {
              Alert.alert('Upload failed', e.message || 'Unknown error');
            }
            router.replace('/');
          }
        }
      } catch (e: any) {
        Alert.alert('Processing failed', e.message || 'Unknown error');
        if (scanMode === 'items') {
          router.replace('/scan-items');
        } else if (scanMode === 'receipt') {
          router.replace('/receipt-scanner');
        } else {
          router.replace('/');
        }
      } finally {
        setLoading(false);
      }
    };
    processImage();
  }, [photoUri, scanMode, imageData, imageKey]);

  const fact = foodFacts[factIndex];

  return (
    <View style={styles.container}>
      <Stack.Screen
        options={{
          headerShown: true,
          header: () => (
            <CustomHeader 
              title="Processing"
              showBackButton={true}
            />
          ),
        }}
      />
      <View style={styles.factBox}>
        <Text style={styles.category}>{fact.category}</Text>
        <Text style={styles.factText}>{fact.text}</Text>
      </View>
      <ActivityIndicator size="large" color="#297A56" style={styles.spinner} />
      <Text style={styles.loadingText}>Analyzing your photo...</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#fff',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 24,
  },
  factBox: {
    marginBottom: 40,
    backgroundColor: '#F4F8F6',
    borderRadius: 12,
    padding: 24,
    maxWidth: 340,
    shadowColor: '#000',
    shadowOpacity: 0.06,
    shadowRadius: 8,
    shadowOffset: { width: 0, height: 2 },
    elevation: 2,
  },
  category: {
    fontWeight: 'bold',
    color: '#297A56',
    fontSize: 16,
    marginBottom: 8,
    textTransform: 'uppercase',
    letterSpacing: 1,
  },
  factText: {
    fontSize: 16,
    color: '#222',
    lineHeight: 22,
  },
  spinner: {
    marginBottom: 24,
  },
  loadingText: {
    color: '#888',
    fontSize: 16,
    marginTop: 8,
  },
}); 