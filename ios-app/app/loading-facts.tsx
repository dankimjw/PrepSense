import React, { useEffect, useRef, useState } from 'react';
import { View, Text, StyleSheet, ActivityIndicator, Alert } from 'react-native';
import { useRouter, useLocalSearchParams } from 'expo-router';
import { foodFacts } from './utils/facts';
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
    }, 5000);
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, []);

  useEffect(() => {
    const uploadAndFetch = async () => {
      try {
        if (!photoUri) throw new Error('No photo URI provided');
        const info = await FileSystem.getInfoAsync(photoUri);
        const body = new FormData();
        body.append('file', {
          uri: photoUri,
          name: info.uri.split('/').pop() ?? 'image.jpg',
          type: 'image/jpeg',
        } as any);

        const r = await fetch(UPLOAD_URL, { method: 'POST', body });
        if (!r.ok) throw new Error(`HTTP ${r.status}`);

        const { pantry_items } = await r.json();
        if (!Array.isArray(pantry_items) || pantry_items.length === 0) {
          Alert.alert('No items detected', 'Try another photo?');
          router.replace('/');
          return;
        }

        const dataParam = Buffer
          .from(JSON.stringify(pantry_items))
          .toString('base64');

        router.replace({
          pathname: '/items-detected',
          params: { data: dataParam, photoUri },
        });
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