import React, { useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, Image, ScrollView, Alert, ActivityIndicator } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import * as ImagePicker from 'expo-image-picker';
import * as ImageManipulator from 'expo-image-manipulator';
import { API_URL } from '../config';

interface ParsedItem {
  name: string;
  quantity: number;
  unit: string;
  price?: number;
  category?: string;
}

export default function ScanReceiptScreen() {
  const router = useRouter();
  const [imageUri, setImageUri] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [parsedItems, setParsedItems] = useState<ParsedItem[]>([]);
  const [selectedItems, setSelectedItems] = useState<Set<number>>(new Set());

  const pickImage = async (useCamera: boolean) => {
    const result = await (useCamera 
      ? ImagePicker.launchCameraAsync({
          allowsEditing: true,
          quality: 1,
        })
      : ImagePicker.launchImageLibraryAsync({
          mediaTypes: ImagePicker.MediaTypeOptions.Images,
          allowsEditing: true,
          quality: 1,
        }));

    if (!result.canceled) {
      setImageUri(result.assets[0].uri);
      setParsedItems([]);
      setSelectedItems(new Set());
    }
  };

  const scanReceipt = async () => {
    if (!imageUri) return;

    setLoading(true);
    try {
      // Resize image to reduce size
      const manipResult = await ImageManipulator.manipulateAsync(
        imageUri,
        [{ resize: { width: 1024 } }],
        { compress: 0.7, format: ImageManipulator.SaveFormat.JPEG, base64: true }
      );

      const response = await fetch(`${API_URL}/ocr/scan-receipt`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          image_base64: manipResult.base64,
          user_id: 111, // Using demo user
        }),
      });

      const data = await response.json();
      
      if (data.success) {
        setParsedItems(data.items);
        // Select all items by default
        setSelectedItems(new Set(data.items.map((_: any, index: number) => index)));
      } else {
        Alert.alert('Error', data.message || 'Failed to scan receipt');
      }
    } catch (error) {
      console.error('Error scanning receipt:', error);
      Alert.alert('Error', 'Failed to scan receipt. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const toggleItemSelection = (index: number) => {
    const newSelection = new Set(selectedItems);
    if (newSelection.has(index)) {
      newSelection.delete(index);
    } else {
      newSelection.add(index);
    }
    setSelectedItems(newSelection);
  };

  const addSelectedItems = async () => {
    const itemsToAdd = parsedItems.filter((_, index) => selectedItems.has(index));
    
    if (itemsToAdd.length === 0) {
      Alert.alert('No Items Selected', 'Please select at least one item to add.');
      return;
    }

    setLoading(true);
    try {
      const response = await fetch(`${API_URL}/ocr/add-scanned-items`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          items: itemsToAdd,
          user_id: 111, // Using demo user
        }),
      });

      const data = await response.json();
      
      if (data.success) {
        Alert.alert(
          'Success', 
          `Added ${data.added_count} out of ${data.total_count} items to pantry.`,
          [{ text: 'OK', onPress: () => router.back() }]
        );
      } else {
        Alert.alert('Error', data.message || 'Failed to add items');
      }
    } catch (error) {
      console.error('Error adding items:', error);
      Alert.alert('Error', 'Failed to add items. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => router.back()} style={styles.backButton}>
          <Ionicons name="arrow-back" size={24} color="#111827" />
        </TouchableOpacity>
        <Text style={styles.title}>Scan Receipt</Text>
        <View style={{ width: 40 }} />
      </View>

      <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
        {!imageUri ? (
          <View style={styles.uploadSection}>
            <Ionicons name="receipt-outline" size={64} color="#9CA3AF" />
            <Text style={styles.uploadTitle}>Upload a receipt to scan</Text>
            <Text style={styles.uploadSubtitle}>Take a photo or choose from gallery</Text>
            
            <View style={styles.buttonRow}>
              <TouchableOpacity 
                style={[styles.uploadButton, { marginRight: 8 }]} 
                onPress={() => pickImage(true)}
              >
                <Ionicons name="camera" size={24} color="white" />
                <Text style={styles.uploadButtonText}>Camera</Text>
              </TouchableOpacity>
              
              <TouchableOpacity 
                style={[styles.uploadButton, { marginLeft: 8 }]} 
                onPress={() => pickImage(false)}
              >
                <Ionicons name="images" size={24} color="white" />
                <Text style={styles.uploadButtonText}>Gallery</Text>
              </TouchableOpacity>
            </View>
          </View>
        ) : (
          <>
            <View style={styles.imageContainer}>
              <Image source={{ uri: imageUri }} style={styles.receiptImage} />
              <TouchableOpacity 
                style={styles.changeImageButton}
                onPress={() => {
                  setImageUri(null);
                  setParsedItems([]);
                  setSelectedItems(new Set());
                }}
              >
                <Text style={styles.changeImageText}>Change Image</Text>
              </TouchableOpacity>
            </View>

            {parsedItems.length === 0 ? (
              <TouchableOpacity 
                style={styles.scanButton}
                onPress={scanReceipt}
                disabled={loading}
              >
                {loading ? (
                  <ActivityIndicator color="white" />
                ) : (
                  <>
                    <Ionicons name="scan" size={24} color="white" />
                    <Text style={styles.scanButtonText}>Scan Receipt</Text>
                  </>
                )}
              </TouchableOpacity>
            ) : (
              <>
                <Text style={styles.sectionTitle}>Found Items</Text>
                <Text style={styles.sectionSubtitle}>Select items to add to your pantry</Text>
                
                {parsedItems.map((item, index) => (
                  <TouchableOpacity
                    key={index}
                    style={[
                      styles.itemCard,
                      selectedItems.has(index) && styles.itemCardSelected
                    ]}
                    onPress={() => toggleItemSelection(index)}
                  >
                    <View style={styles.itemCheckbox}>
                      {selectedItems.has(index) && (
                        <Ionicons name="checkmark" size={18} color="#297A56" />
                      )}
                    </View>
                    
                    <View style={styles.itemInfo}>
                      <Text style={styles.itemName}>{item.name}</Text>
                      <Text style={styles.itemDetails}>
                        {item.quantity} {item.unit}
                        {item.price && ` • $${item.price.toFixed(2)}`}
                      </Text>
                      {item.category && (
                        <Text style={styles.itemCategory}>{item.category}</Text>
                      )}
                    </View>
                  </TouchableOpacity>
                ))}

                <View style={styles.actionButtons}>
                  <TouchableOpacity 
                    style={[styles.actionButton, styles.cancelButton]}
                    onPress={() => {
                      setParsedItems([]);
                      setSelectedItems(new Set());
                    }}
                  >
                    <Text style={styles.cancelButtonText}>Clear</Text>
                  </TouchableOpacity>
                  
                  <TouchableOpacity 
                    style={[styles.actionButton, styles.addButton]}
                    onPress={addSelectedItems}
                    disabled={loading || selectedItems.size === 0}
                  >
                    {loading ? (
                      <ActivityIndicator color="white" />
                    ) : (
                      <Text style={styles.addButtonText}>
                        Add {selectedItems.size} Item{selectedItems.size !== 1 ? 's' : ''}
                      </Text>
                    )}
                  </TouchableOpacity>
                </View>
              </>
            )}
          </>
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F3F4F6',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 12,
    backgroundColor: 'white',
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
  },
  backButton: {
    width: 40,
    height: 40,
    justifyContent: 'center',
    alignItems: 'center',
  },
  title: {
    fontSize: 18,
    fontWeight: '600',
    color: '#111827',
  },
  content: {
    flex: 1,
    padding: 16,
  },
  uploadSection: {
    backgroundColor: 'white',
    borderRadius: 12,
    padding: 32,
    alignItems: 'center',
    marginTop: 24,
  },
  uploadTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#111827',
    marginTop: 16,
  },
  uploadSubtitle: {
    fontSize: 14,
    color: '#6B7280',
    marginTop: 4,
  },
  buttonRow: {
    flexDirection: 'row',
    marginTop: 24,
  },
  uploadButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#297A56',
    paddingHorizontal: 20,
    paddingVertical: 12,
    borderRadius: 8,
  },
  uploadButtonText: {
    color: 'white',
    fontWeight: '600',
    marginLeft: 8,
  },
  imageContainer: {
    backgroundColor: 'white',
    borderRadius: 12,
    padding: 12,
    marginBottom: 16,
  },
  receiptImage: {
    width: '100%',
    height: 300,
    borderRadius: 8,
    resizeMode: 'contain',
  },
  changeImageButton: {
    marginTop: 8,
    paddingVertical: 8,
    alignItems: 'center',
  },
  changeImageText: {
    color: '#297A56',
    fontWeight: '600',
  },
  scanButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#297A56',
    padding: 16,
    borderRadius: 8,
    marginBottom: 24,
  },
  scanButtonText: {
    color: 'white',
    fontWeight: '600',
    fontSize: 16,
    marginLeft: 8,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#111827',
    marginBottom: 4,
  },
  sectionSubtitle: {
    fontSize: 14,
    color: '#6B7280',
    marginBottom: 16,
  },
  itemCard: {
    flexDirection: 'row',
    backgroundColor: 'white',
    borderRadius: 8,
    padding: 16,
    marginBottom: 8,
    borderWidth: 2,
    borderColor: 'transparent',
  },
  itemCardSelected: {
    borderColor: '#297A56',
  },
  itemCheckbox: {
    width: 24,
    height: 24,
    borderRadius: 4,
    borderWidth: 2,
    borderColor: '#D1D5DB',
    marginRight: 12,
    justifyContent: 'center',
    alignItems: 'center',
  },
  itemInfo: {
    flex: 1,
  },
  itemName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#111827',
  },
  itemDetails: {
    fontSize: 14,
    color: '#6B7280',
    marginTop: 2,
  },
  itemCategory: {
    fontSize: 12,
    color: '#297A56',
    marginTop: 4,
    backgroundColor: '#297A5615',
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 4,
    alignSelf: 'flex-start',
  },
  actionButtons: {
    flexDirection: 'row',
    marginTop: 24,
    gap: 12,
  },
  actionButton: {
    flex: 1,
    paddingVertical: 16,
    borderRadius: 8,
    alignItems: 'center',
  },
  cancelButton: {
    backgroundColor: '#E5E7EB',
  },
  cancelButtonText: {
    color: '#374151',
    fontWeight: '600',
  },
  addButton: {
    backgroundColor: '#297A56',
  },
  addButtonText: {
    color: 'white',
    fontWeight: '600',
  },
});