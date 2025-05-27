// app/loading-facts.tsx - Part of the PrepSense mobile app
import React, { useEffect, useRef, useState } from 'react';
import { View, Text, StyleSheet, ActivityIndicator, Alert } from 'react-native';
import { useRouter, useLocalSearchParams, Stack } from 'expo-router';
import { foodFacts } from './utils/facts';
import { CustomHeader } from './components/CustomHeader';
import * as FileSystem from 'expo-file-system';
import { Buffer } from 'buffer';
import { Config } from '../config';

const UPLOAD_URL = `${Config.API_BASE_URL}/images/upload`;

export default function LoadingFactsScreen() {
  const [factIndex, setFactIndex] = useState(() => Math.floor(Math.random() * foodFacts.length));
  const [loading, setLoading] = useState(true);
  const intervalRef = useRef<any>(null);
  const router = useRouter();
  const { photoUri } = useLocalSearchParams<{ photoUri: string }>();

  useEffect(() => {
    intervalRef.current = setInterval(() => {
      setFactIndex((prev) => (prev + 1) % foodFacts.length);
    }, 4000);
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, []);

  useEffect(() => {
    const uploadAndFetch = async () => {
      try {
        if (!photoUri) throw new Error('No photo URI provided');
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
      } catch (e: any) {
        Alert.alert('Upload failed', e.message || 'Unknown error');
        router.replace('/');
      } finally {
        setLoading(false);
      }
    };
    uploadAndFetch();
  }, [photoUri]);

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