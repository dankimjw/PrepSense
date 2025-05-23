import * as ImagePicker from 'expo-image-picker';
// Tip: on the iOS simulator you can drag images from your Mac straight onto the
// simulator window. They appear in the Photos app for easy selection.
import * as FileSystem from 'expo-file-system';
import { Buffer } from 'buffer';
import {
  View,
  Image,
  StyleSheet,
  Pressable,
  Text,
  Platform,
  Alert,
  ActivityIndicator,
} from 'react-native';
import { useRouter, useLocalSearchParams } from 'expo-router';
import { useState, useEffect } from 'react';
import { Ionicons } from '@expo/vector-icons';

import { Config } from '../config';
const UPLOAD_URL = `${Config.API_BASE_URL}/images/upload`;

export default function Camera() {
  const router = useRouter();
  const { action } = useLocalSearchParams<{ action?: string }>();

  const [uri,   setUri] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  /* permissions */
  useEffect(() => {
    (async () => {
      if (Platform.OS !== 'web') {
        await ImagePicker.requestCameraPermissionsAsync();
        await ImagePicker.requestMediaLibraryPermissionsAsync();
      }
    })();
  }, []);

  /* reset coming back from items-detected */
  useEffect(() => {
    if (action === 'reset_image') setUri(null);
  }, [action]);

  const pick = async () => {
    const res = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      quality: 0.8,
    });
    if (!res.canceled) setUri(res.assets[0].uri);
  };

  const shoot = async () => {
    const res = await ImagePicker.launchCameraAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      quality: 0.8,
    });
    if (!res.canceled) setUri(res.assets[0].uri);
  };

  /* ---------- SINGLE confirm ---------- */
  const confirmOnce = async () => {
    if (!uri || busy) return;
    try {
      setBusy(true);

      const info = await FileSystem.getInfoAsync(uri);
      const body = new FormData();
      body.append('file', {
        uri,
        name: info.uri.split('/').pop() ?? 'image.jpg',
        type: 'image/jpeg',
      } as any);

      const r = await fetch(UPLOAD_URL, { method: 'POST', body });
      if (!r.ok) throw new Error(`HTTP ${r.status}`);

      const { pantry_items } = await r.json();
      if (!Array.isArray(pantry_items) || pantry_items.length === 0) {
        Alert.alert('No items detected', 'Try another photo?');
        return;
      }

      const param = Buffer.from(JSON.stringify(pantry_items)).toString('base64');

      router.push({
        pathname: '/items-detected',
        params: { data: param, photoUri: uri },
      });
    } catch (e: any) {
      console.error(e);
      Alert.alert('Upload failed', e.message);
    } finally {
      setBusy(false);
    }
  };

  const retake = () => setUri(null);

  return (
    <View style={styles.container}>
      {/* image frame */}
      <View style={styles.frame}>
        {uri ? (
          <Image source={{ uri }} style={styles.preview} />
        ) : (
          <>
            <Ionicons name="image-outline" size={48} color="#aaa" />
            <Text style={styles.placeholder}>No image selected</Text>
          </>
        )}

        {busy && (
          <View style={styles.overlay}>
            <ActivityIndicator size="large" />
          </View>
        )}
      </View>

      {/* buttons */}
      {!uri ? (
        <View style={styles.buttons}>
          <Pressable style={styles.iconBtn} onPress={shoot} disabled={busy}>
            <Ionicons name="camera" size={24} color="#fff" />
          </Pressable>
          <Pressable style={styles.mainBtn} onPress={pick} disabled={busy}>
            <Text style={styles.mainTxt}>Upload Image</Text>
          </Pressable>
        </View>
      ) : (
        <View style={styles.row}>
          <Pressable style={styles.mainBtn} onPress={retake} disabled={busy}>
            <Text style={styles.mainTxt}>Retake</Text>
          </Pressable>
          {/* 🔑 this is now confirmOnce */}
          <Pressable style={styles.mainBtn} onPress={confirmOnce} disabled={busy}>
            <Text style={styles.mainTxt}>Confirm</Text>
          </Pressable>
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, justifyContent: 'center', alignItems: 'center', gap: 16 },
  frame: {
    width: 280, height: 280, borderWidth: 1, borderColor: '#ccc', borderRadius: 12,
    justifyContent: 'center', alignItems: 'center', backgroundColor: '#fff', overflow: 'hidden',
  },
  preview: { width: '100%', height: '100%', resizeMode: 'cover' },
  placeholder: { marginTop: 8, color: '#aaa' },
  buttons: { flexDirection: 'row', gap: 12 },
  row: { flexDirection: 'row', gap: 20 },
  mainBtn: {
    backgroundColor: '#297A56', paddingVertical: 12, paddingHorizontal: 20, borderRadius: 8,
  },
  mainTxt: { color: '#fff', fontWeight: 'bold' },
  iconBtn: {
    backgroundColor: '#297A56', padding: 12, borderRadius: 8, alignItems: 'center', justifyContent: 'center',
  },
  overlay: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: 'rgba(255,255,255,0.6)',
    justifyContent: 'center',
    alignItems: 'center',
  },
});
