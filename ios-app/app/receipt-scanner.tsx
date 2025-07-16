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
  Modal,
  FlatList,
  TextInput,
} from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons, MaterialIcons } from '@expo/vector-icons';
import * as ImagePicker from 'expo-image-picker';
import { Config } from '../config';
import { LinearGradient } from 'expo-linear-gradient';

interface ScannedItem {
  name: string;
  quantity: number;
  unit: string;
  price?: number;
  category?: string;
  selected: boolean;
}

export default function ReceiptScannerScreen() {
  const router = useRouter();
  const [image, setImage] = useState<string | null>(null);
  const [isScanning, setIsScanning] = useState(false);
  const [scannedItems, setScannedItems] = useState<ScannedItem[]>([]);
  const [showEditModal, setShowEditModal] = useState(false);
  const [editingItem, setEditingItem] = useState<ScannedItem | null>(null);
  const [editingIndex, setEditingIndex] = useState<number>(-1);
  const [isAdding, setIsAdding] = useState(false);

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
        // Add selected property to each item
        const itemsWithSelection = data.items.map((item: any) => ({
          ...item,
          selected: true,
        }));
        setScannedItems(itemsWithSelection);
        
        Alert.alert(
          'Scan Complete',
          `Found ${data.items.length} items. Review and edit before adding to pantry.`,
          [{ text: 'OK' }]
        );
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

  const toggleItemSelection = (index: number) => {
    const updated = [...scannedItems];
    updated[index].selected = !updated[index].selected;
    setScannedItems(updated);
  };

  const editItem = (item: ScannedItem, index: number) => {
    setEditingItem({ ...item });
    setEditingIndex(index);
    setShowEditModal(true);
  };

  const saveEditedItem = () => {
    if (editingItem && editingIndex >= 0) {
      const updated = [...scannedItems];
      updated[editingIndex] = { ...editingItem };
      setScannedItems(updated);
      setShowEditModal(false);
      setEditingItem(null);
      setEditingIndex(-1);
    }
  };

  const addItemsToPantry = async () => {
    const selectedItems = scannedItems.filter(item => item.selected);
    
    if (selectedItems.length === 0) {
      Alert.alert('No Items Selected', 'Please select at least one item to add.');
      return;
    }

    setIsAdding(true);

    try {
      const response = await fetch(`${Config.API_BASE_URL}/ocr/add-scanned-items`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(selectedItems),
      });

      if (!response.ok) {
        throw new Error('Failed to add items');
      }

      const result = await response.json();
      
      Alert.alert(
        'Items Added',
        result.message,
        [
          {
            text: 'View Pantry',
            onPress: () => router.replace('/(tabs)'),
          },
          {
            text: 'Scan Another',
            onPress: () => {
              setImage(null);
              setScannedItems([]);
            },
          },
        ]
      );
    } catch (error) {
      console.error('Error adding items:', error);
      Alert.alert('Error', 'Failed to add items to pantry. Please try again.');
    } finally {
      setIsAdding(false);
    }
  };

  const renderScannedItem = ({ item, index }: { item: ScannedItem; index: number }) => (
    <TouchableOpacity
      style={[styles.itemCard, !item.selected && styles.itemCardUnselected]}
      onPress={() => toggleItemSelection(index)}
    >
      <TouchableOpacity
        style={styles.checkbox}
        onPress={() => toggleItemSelection(index)}
      >
        <Ionicons
          name={item.selected ? 'checkbox' : 'square-outline'}
          size={24}
          color={item.selected ? '#297A56' : '#999'}
        />
      </TouchableOpacity>
      
      <View style={styles.itemInfo}>
        <Text style={[styles.itemName, !item.selected && styles.itemNameUnselected]}>
          {item.name}
        </Text>
        <View style={styles.itemDetails}>
          <Text style={styles.itemQuantity}>
            {item.quantity} {item.unit}
          </Text>
          {item.category && (
            <View style={styles.categoryBadge}>
              <Text style={styles.categoryText}>{item.category}</Text>
            </View>
          )}
          {item.price && (
            <Text style={styles.itemPrice}>${item.price.toFixed(2)}</Text>
          )}
        </View>
      </View>
      
      <TouchableOpacity
        style={styles.editButton}
        onPress={() => editItem(item, index)}
      >
        <Ionicons name="pencil" size={20} color="#297A56" />
      </TouchableOpacity>
    </TouchableOpacity>
  );

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

            {scannedItems.length > 0 && (
              <>
                <View style={styles.resultsHeader}>
                  <Text style={styles.resultsTitle}>Scanned Items</Text>
                  <TouchableOpacity
                    style={styles.selectAllButton}
                    onPress={() => {
                      const allSelected = scannedItems.every(item => item.selected);
                      setScannedItems(scannedItems.map(item => ({ ...item, selected: !allSelected })));
                    }}
                  >
                    <Text style={styles.selectAllText}>
                      {scannedItems.every(item => item.selected) ? 'Deselect All' : 'Select All'}
                    </Text>
                  </TouchableOpacity>
                </View>

                <FlatList
                  data={scannedItems}
                  renderItem={renderScannedItem}
                  keyExtractor={(item, index) => `${item.name}-${index}`}
                  style={styles.itemsList}
                  scrollEnabled={false}
                />

                <View style={styles.actionButtons}>
                  <TouchableOpacity
                    style={styles.rescanButton}
                    onPress={() => {
                      setImage(null);
                      setScannedItems([]);
                    }}
                  >
                    <Ionicons name="refresh" size={20} color="#666" />
                    <Text style={styles.rescanText}>Scan New Receipt</Text>
                  </TouchableOpacity>

                  <TouchableOpacity
                    style={[styles.addButton, isAdding && styles.addButtonDisabled]}
                    onPress={addItemsToPantry}
                    disabled={isAdding}
                  >
                    {isAdding ? (
                      <ActivityIndicator size="small" color="#fff" />
                    ) : (
                      <>
                        <Ionicons name="add-circle" size={20} color="#fff" />
                        <Text style={styles.addButtonText}>
                          Add {scannedItems.filter(item => item.selected).length} Items
                        </Text>
                      </>
                    )}
                  </TouchableOpacity>
                </View>
              </>
            )}
          </View>
        )}
      </ScrollView>

      {/* Edit Modal */}
      <Modal
        visible={showEditModal}
        transparent
        animationType="slide"
        onRequestClose={() => setShowEditModal(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>Edit Item</Text>
            
            {editingItem && (
              <>
                <Text style={styles.inputLabel}>Name</Text>
                <TextInput
                  style={styles.input}
                  value={editingItem.name}
                  onChangeText={(text) => setEditingItem({ ...editingItem, name: text })}
                  placeholder="Item name"
                />

                <View style={styles.row}>
                  <View style={styles.halfInput}>
                    <Text style={styles.inputLabel}>Quantity</Text>
                    <TextInput
                      style={styles.input}
                      value={editingItem.quantity.toString()}
                      onChangeText={(text) => {
                        const num = parseFloat(text) || 0;
                        setEditingItem({ ...editingItem, quantity: num });
                      }}
                      keyboardType="numeric"
                      placeholder="1"
                    />
                  </View>
                  
                  <View style={styles.halfInput}>
                    <Text style={styles.inputLabel}>Unit</Text>
                    <TextInput
                      style={styles.input}
                      value={editingItem.unit}
                      onChangeText={(text) => setEditingItem({ ...editingItem, unit: text })}
                      placeholder="each"
                    />
                  </View>
                </View>

                <View style={styles.modalButtons}>
                  <TouchableOpacity
                    style={styles.cancelButton}
                    onPress={() => setShowEditModal(false)}
                  >
                    <Text style={styles.cancelButtonText}>Cancel</Text>
                  </TouchableOpacity>
                  
                  <TouchableOpacity
                    style={styles.saveButton}
                    onPress={saveEditedItem}
                  >
                    <Text style={styles.saveButtonText}>Save</Text>
                  </TouchableOpacity>
                </View>
              </>
            )}
          </View>
        </View>
      </Modal>
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
  resultsHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  resultsTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: '#333',
  },
  selectAllButton: {
    padding: 8,
  },
  selectAllText: {
    color: '#297A56',
    fontSize: 14,
    fontWeight: '600',
  },
  itemsList: {
    marginBottom: 20,
  },
  itemCard: {
    flexDirection: 'row',
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 2,
  },
  itemCardUnselected: {
    opacity: 0.6,
  },
  checkbox: {
    marginRight: 12,
  },
  itemInfo: {
    flex: 1,
  },
  itemName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
    marginBottom: 4,
  },
  itemNameUnselected: {
    color: '#999',
  },
  itemDetails: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  itemQuantity: {
    fontSize: 14,
    color: '#666',
  },
  categoryBadge: {
    backgroundColor: '#e0f2f1',
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 4,
  },
  categoryText: {
    fontSize: 12,
    color: '#297A56',
  },
  itemPrice: {
    fontSize: 14,
    color: '#666',
    fontWeight: '600',
  },
  editButton: {
    padding: 8,
  },
  actionButtons: {
    flexDirection: 'row',
    gap: 12,
    marginTop: 20,
  },
  rescanButton: {
    flex: 1,
    flexDirection: 'row',
    backgroundColor: '#fff',
    paddingVertical: 16,
    paddingHorizontal: 16,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    borderWidth: 1,
    borderColor: '#e0e0e0',
  },
  rescanText: {
    fontSize: 16,
    color: '#666',
    fontWeight: '500',
  },
  addButton: {
    flex: 1,
    flexDirection: 'row',
    backgroundColor: '#297A56',
    paddingVertical: 16,
    paddingHorizontal: 16,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
  },
  addButtonDisabled: {
    opacity: 0.5,
  },
  addButtonText: {
    fontSize: 16,
    color: '#fff',
    fontWeight: '600',
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.5)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  modalContent: {
    backgroundColor: '#fff',
    borderRadius: 16,
    padding: 24,
    width: '90%',
    maxWidth: 400,
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: '#333',
    marginBottom: 20,
  },
  inputLabel: {
    fontSize: 14,
    color: '#666',
    marginBottom: 8,
    fontWeight: '500',
  },
  input: {
    borderWidth: 1,
    borderColor: '#e0e0e0',
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
    marginBottom: 16,
  },
  row: {
    flexDirection: 'row',
    gap: 12,
  },
  halfInput: {
    flex: 1,
  },
  modalButtons: {
    flexDirection: 'row',
    gap: 12,
    marginTop: 20,
  },
  cancelButton: {
    flex: 1,
    paddingVertical: 12,
    borderRadius: 8,
    alignItems: 'center',
    backgroundColor: '#f0f0f0',
  },
  cancelButtonText: {
    fontSize: 16,
    color: '#666',
    fontWeight: '500',
  },
  saveButton: {
    flex: 1,
    paddingVertical: 12,
    borderRadius: 8,
    alignItems: 'center',
    backgroundColor: '#297A56',
  },
  saveButtonText: {
    fontSize: 16,
    color: '#fff',
    fontWeight: '600',
  },
});