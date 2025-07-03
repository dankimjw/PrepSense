// app/components/AddButton.tsx - Part of the PrepSense mobile app
import { Ionicons } from '@expo/vector-icons';
import { Pressable, StyleSheet, Dimensions, View, Modal, Text, TouchableOpacity } from 'react-native';
import { useRouter, usePathname } from 'expo-router';
import { useState } from 'react';

// Get screen width to calculate tab positions
const { width: SCREEN_WIDTH } = Dimensions.get('window');
const TAB_BAR_HEIGHT = 72; // From tab bar styles
const FAB_SIZE = 48; // Reduced from 56
const FAB_MARGIN = 16;

export function AddButton() {
  const router = useRouter();
  const pathname = usePathname();
  const [modalVisible, setModalVisible] = useState(false);

  // Don't render the add button on certain screens
  if (pathname === '/add-item' || pathname === '/upload-photo' || pathname === '/(tabs)/admin') {
    return null;
  }

  const handleAddImage = () => {
    setModalVisible(false);
    router.push('/upload-photo');
  };

  const handleAddFoodItem = () => {
    setModalVisible(false);
    router.push('/add-item');
  };

  return (
    <>
      <Pressable
        onPress={() => setModalVisible(true)}
        style={styles.fab}>
        <Ionicons name="add" size={28} color="#fff" />
      </Pressable>

      <Modal
        visible={modalVisible}
        transparent
        animationType="fade"
        onRequestClose={() => setModalVisible(false)}
      >
        <Pressable style={styles.modalOverlay} onPress={() => setModalVisible(false)}>
          <View style={styles.modalContent}>
            <TouchableOpacity style={styles.modalBtn} onPress={handleAddImage}>
              <Ionicons name="image" size={22} color="#297A56" />
              <Text style={styles.modalBtnText}>Add Image</Text>
            </TouchableOpacity>
            <TouchableOpacity style={styles.modalBtn} onPress={handleAddFoodItem}>
              <Ionicons name="fast-food" size={22} color="#297A56" />
              <Text style={styles.modalBtnText}>Add Food Item</Text>
            </TouchableOpacity>
          </View>
        </Pressable>
      </Modal>
    </>
  );
}

const styles = StyleSheet.create({
  fab: {
    position: 'absolute',
    bottom: TAB_BAR_HEIGHT + FAB_MARGIN,
    right: FAB_MARGIN,
    width: FAB_SIZE,
    height: FAB_SIZE,
    borderRadius: FAB_SIZE / 2,
    backgroundColor: '#297A56',
    alignItems: 'center',
    justifyContent: 'center',
    elevation: 8,
    shadowColor: '#297A56',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 3.84,
    zIndex: 10,
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.2)',
    justifyContent: 'flex-end',
    alignItems: 'flex-end',
  },
  modalContent: {
    backgroundColor: '#fff',
    borderRadius: 16,
    padding: 16,
    marginBottom: TAB_BAR_HEIGHT + FAB_SIZE + FAB_MARGIN * 2,
    marginRight: FAB_MARGIN,
    width: 200,
    shadowColor: '#000',
    shadowOpacity: 0.1,
    shadowRadius: 12,
    shadowOffset: { width: 0, height: 4 },
    elevation: 12,
  },
  modalBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 14,
    paddingHorizontal: 10,
    borderRadius: 8,
    marginBottom: 8,
  },
  modalBtnText: {
    fontSize: 16,
    color: '#297A56',
    marginLeft: 12,
    fontWeight: '600',
  },
});