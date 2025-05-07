import * as ImagePicker from 'expo-image-picker';
import { useState } from 'react';
import { View, Image, StyleSheet, Pressable, Text } from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';

export default function CameraScreen() {
  const router = useRouter();
  const [uri, setUri] = useState<string | null>(null);

  /* ---- pick a file from gallery ---- */
  async function uploadFile() {
    const res = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      quality: 0.8,
    });
    if (!res.canceled) {
      setUri(res.assets[0].uri); // sets state; UI re-renders
    }
  }

  /* ---- launch camera ---- */
  async function launchCamera() {
    const res = await ImagePicker.launchCameraAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      quality: 0.8,
    });
    if (!res.canceled) {
      setUri(res.assets[0].uri);
    }
  }

  /* ---- reset photo ---- */
  function retake() {
    setUri(null); // clears state; white box shows
  }

  /* ---- go to confirm screen ---- */
  function confirm() {
    if (uri) {
      router.push({ pathname: '/confirm', params: { photoUri: uri } });
    }
  }

  const styles = StyleSheet.create({
    container: { flex: 1, justifyContent: 'center', alignItems: 'center', gap: 16, padding: 20 },
    frame: {
      width: 280,
      height: 280,
      borderWidth: 1,
      borderColor: '#ccc',
      borderRadius: 12,
      justifyContent: 'center',
      alignItems: 'center',
      backgroundColor: '#fff',
    },
    preview: { width: '100%', height: '100%', borderRadius: 12, resizeMode: 'cover' },
    row: { flexDirection: 'row', gap: 20, marginTop: 10 },
    buttonRow: {
      flexDirection: 'row',
      gap: 12,
      alignItems: 'center',
    },
    uploadButton: {
      backgroundColor: '#297A56', // Custom green color
      paddingVertical: 12,
      paddingHorizontal: 20,
      borderRadius: 8,
      alignItems: 'center',
    },
    uploadButtonText: {
      color: '#fff', // White font color
      fontSize: 16,
      fontWeight: 'bold',
    },
    cameraButton: {
      backgroundColor: '#297A56',
      padding: 12,
      borderRadius: 8,
      alignItems: 'center',
      justifyContent: 'center',
    },
  });

  return (
    <View style={styles.container}>
      {/* White box or image */}
      <View style={styles.frame}>
        {uri ? (
          <Image source={{ uri }} style={styles.preview} />
        ) : (
          <Ionicons name="image-outline" size={48} color="#aaa" />
        )}
      </View>

      {/* Show Camera and Upload buttons only if no image is selected */}
      {!uri && (
        <View style={styles.buttonRow}>
          {/* Camera Icon / Button */}
          <Pressable style={styles.cameraButton} onPress={launchCamera}>
            <Ionicons name="camera" size={24} color="#fff" />
          </Pressable>

          {/* Custom Upload Image button */}
          <Pressable style={styles.uploadButton} onPress={uploadFile}>
            <Text style={styles.uploadButtonText}>Upload Image</Text>
          </Pressable>
        </View>
      )}

      {/* Show Retake / Confirm buttons only if an image is selected */}
      {uri && (
        <View style={styles.row}>
          {/* Retake Button */}
          <Pressable style={styles.uploadButton} onPress={retake}>
            <Text style={styles.uploadButtonText}>Retake</Text>
          </Pressable>

          {/* Confirm Button */}
          <Pressable style={styles.uploadButton} onPress={confirm}>
            <Text style={styles.uploadButtonText}>Confirm</Text>
          </Pressable>
        </View>
      )}
    </View>
  );
}