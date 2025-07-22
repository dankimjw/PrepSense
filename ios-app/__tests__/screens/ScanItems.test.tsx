/**
 * Tests for ScanItemsScreen component
 * Tests barcode/product scanning, image capture, and item detection
 */

import React from 'react';
import { render, fireEvent, waitFor } from '@testing-library/react-native';
import { Alert } from 'react-native';
import * as ImagePicker from 'expo-image-picker';
import { useRouter } from 'expo-router';
import { useAuth } from '../../context/AuthContext';
import { Buffer } from 'buffer';
import ScanItemsScreen from '../../app/scan-items';

// Mock dependencies
jest.mock('expo-router', () => ({
  useRouter: jest.fn(),
}));

jest.mock('../../context/AuthContext', () => ({
  useAuth: jest.fn(),
}));

jest.mock('expo-image-picker', () => ({
  requestCameraPermissionsAsync: jest.fn(),
  requestMediaLibraryPermissionsAsync: jest.fn(),
  launchCameraAsync: jest.fn(),
  launchImageLibraryAsync: jest.fn(),
  MediaTypeOptions: {
    Images: 'Images',
  },
}));

jest.mock('react-native/Libraries/Alert/Alert', () => ({
  alert: jest.fn(),
}));

jest.mock('../../config', () => ({
  Config: {
    API_BASE_URL: 'http://test-api',
  },
}));

jest.mock('expo-linear-gradient', () => ({
  LinearGradient: ({ children }: any) => children,
}));

// Mock fetch
global.fetch = jest.fn();

describe('ScanItemsScreen', () => {
  let mockRouter: any;
  let mockUser: any;
  
  beforeEach(() => {
    jest.clearAllMocks();
    mockRouter = {
      back: jest.fn(),
      replace: jest.fn(),
    };
    mockUser = {
      id: 123,
    };
    (useRouter as jest.Mock).mockReturnValue(mockRouter);
    (useAuth as jest.Mock).mockReturnValue({ user: mockUser });
    (global.fetch as jest.Mock).mockReset();
    
    // Mock permissions as granted by default
    (ImagePicker.requestCameraPermissionsAsync as jest.Mock).mockResolvedValue({ status: 'granted' });
    (ImagePicker.requestMediaLibraryPermissionsAsync as jest.Mock).mockResolvedValue({ status: 'granted' });
  });

  describe('Initial State and Permissions', () => {
    it('should render initial scan view', () => {
      const { getByText } = render(<ScanItemsScreen />);
      
      expect(getByText('Scan Items')).toBeTruthy();
      expect(getByText('Scan Your Items')).toBeTruthy();
      expect(getByText('Take a photo of product barcodes or labels to quickly add items to your pantry')).toBeTruthy();
      expect(getByText('Take Photo')).toBeTruthy();
      expect(getByText('Choose from Gallery')).toBeTruthy();
    });

    it('should request permissions on mount', async () => {
      render(<ScanItemsScreen />);
      
      await waitFor(() => {
        expect(ImagePicker.requestCameraPermissionsAsync).toHaveBeenCalled();
        expect(ImagePicker.requestMediaLibraryPermissionsAsync).toHaveBeenCalled();
      });
    });

    it('should show alert when permissions are denied', async () => {
      (ImagePicker.requestCameraPermissionsAsync as jest.Mock).mockResolvedValue({ status: 'denied' });
      (ImagePicker.requestMediaLibraryPermissionsAsync as jest.Mock).mockResolvedValue({ status: 'denied' });
      
      render(<ScanItemsScreen />);
      
      await waitFor(() => {
        expect(Alert.alert).toHaveBeenCalledWith(
          'Permissions Required',
          'Camera and photo library permissions are required to scan items.',
          expect.arrayContaining([{ text: 'OK' }])
        );
      });
    });

    it('should navigate back when back button is pressed', () => {
      const { getAllByTestId } = render(<ScanItemsScreen />);
      
      // Find the back button (arrow-back icon)
      const backButton = getAllByTestId('RNE__ICON')[0].parent;
      fireEvent.press(backButton);
      
      expect(mockRouter.back).toHaveBeenCalled();
    });
  });

  describe('Image Capture', () => {
    it('should open camera when Take Photo button is pressed', async () => {
      const { getByText } = render(<ScanItemsScreen />);
      
      const mockCameraResult = {
        canceled: false,
        assets: [{
          uri: 'camera://photo.jpg',
          base64: 'mockBase64ImageData',
        }],
      };
      (ImagePicker.launchCameraAsync as jest.Mock).mockResolvedValue(mockCameraResult);
      
      // Mock successful scan response
      const mockScanResponse = {
        success: true,
        items: [{
          name: 'Test Product',
          quantity: 1,
          unit: 'box',
          category: 'Pantry',
        }],
      };
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockScanResponse,
      });
      
      fireEvent.press(getByText('Take Photo'));
      
      await waitFor(() => {
        expect(ImagePicker.launchCameraAsync).toHaveBeenCalledWith({
          mediaTypes: 'Images',
          allowsEditing: true,
          quality: 0.8,
          base64: true,
        });
      });
    });

    it('should open gallery when Choose from Gallery button is pressed', async () => {
      const { getByText } = render(<ScanItemsScreen />);
      
      const mockGalleryResult = {
        canceled: false,
        assets: [{
          uri: 'gallery://photo.jpg',
          base64: 'mockBase64ImageData',
        }],
      };
      (ImagePicker.launchImageLibraryAsync as jest.Mock).mockResolvedValue(mockGalleryResult);
      
      // Mock successful scan response
      const mockScanResponse = {
        success: true,
        items: [{
          name: 'Test Product',
          quantity: 1,
          unit: 'box',
        }],
      };
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockScanResponse,
      });
      
      fireEvent.press(getByText('Choose from Gallery'));
      
      await waitFor(() => {
        expect(ImagePicker.launchImageLibraryAsync).toHaveBeenCalledWith({
          mediaTypes: 'Images',
          allowsEditing: true,
          quality: 0.8,
          base64: true,
        });
      });
    });

    it('should do nothing when image picker is canceled', async () => {
      const { getByText } = render(<ScanItemsScreen />);
      
      const mockCanceledResult = {
        canceled: true,
      };
      (ImagePicker.launchCameraAsync as jest.Mock).mockResolvedValue(mockCanceledResult);
      
      fireEvent.press(getByText('Take Photo'));
      
      await waitFor(() => {
        expect(global.fetch).not.toHaveBeenCalled();
      });
    });
  });

  describe('Item Scanning', () => {
    it('should scan item and navigate to results on success', async () => {
      const { getByText } = render(<ScanItemsScreen />);
      
      const mockImageResult = {
        canceled: false,
        assets: [{
          uri: 'test://image.jpg',
          base64: 'mockBase64ImageData',
        }],
      };
      (ImagePicker.launchCameraAsync as jest.Mock).mockResolvedValue(mockImageResult);
      
      // Mock successful scan with barcode data
      const mockScanResponse = {
        success: true,
        items: [{
          name: 'Cheerios',
          product_name: 'General Mills Cheerios',
          quantity: 1,
          unit: 'box',
          category: 'Pantry',
          barcode: '016000275270',
          brand: 'General Mills',
          nutrition_info: {
            calories: 100,
            protein: '3g',
          },
          expiration_date: '2024-06-01',
        }],
      };
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockScanResponse,
      });
      
      fireEvent.press(getByText('Take Photo'));
      
      await waitFor(() => {
        // Verify API call
        expect(global.fetch).toHaveBeenCalledWith(
          'http://test-api/ocr/scan-items',
          expect.objectContaining({
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              image_base64: 'mockBase64ImageData',
              user_id: 123,
              scan_type: 'pantry_item',
            }),
          })
        );
        
        // Verify navigation to items-detected
        expect(mockRouter.replace).toHaveBeenCalled();
        const navCall = mockRouter.replace.mock.calls[0][0];
        expect(navCall.pathname).toBe('/items-detected');
        expect(navCall.params.source).toBe('scan-items');
        expect(navCall.params.photoUri).toBe('test://image.jpg');
        
        // Verify data transformation
        const decodedData = JSON.parse(Buffer.from(navCall.params.data, 'base64').toString());
        expect(decodedData[0]).toMatchObject({
          item_name: 'General Mills Cheerios',
          quantity_amount: 1,
          quantity_unit: 'box',
          category: 'Pantry',
          barcode: '016000275270',
          brand: 'General Mills',
          expected_expiration: '2024-06-01',
        });
      });
    });

    it('should show alert when no items are found', async () => {
      const { getByText } = render(<ScanItemsScreen />);
      
      const mockImageResult = {
        canceled: false,
        assets: [{
          uri: 'test://image.jpg',
          base64: 'mockBase64ImageData',
        }],
      };
      (ImagePicker.launchCameraAsync as jest.Mock).mockResolvedValue(mockImageResult);
      
      // Mock response with no items
      const mockEmptyResponse = {
        success: true,
        items: [],
      };
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockEmptyResponse,
      });
      
      fireEvent.press(getByText('Take Photo'));
      
      await waitFor(() => {
        expect(Alert.alert).toHaveBeenCalledWith(
          'No Items Found',
          'Could not identify the item. Try taking a clearer photo of the product label or barcode.',
          expect.arrayContaining([{ text: 'OK' }])
        );
      });
    });

    it('should handle scan errors gracefully', async () => {
      const { getByText } = render(<ScanItemsScreen />);
      
      const mockImageResult = {
        canceled: false,
        assets: [{
          uri: 'test://image.jpg',
          base64: 'mockBase64ImageData',
        }],
      };
      (ImagePicker.launchCameraAsync as jest.Mock).mockResolvedValue(mockImageResult);
      
      // Mock network error
      (global.fetch as jest.Mock).mockRejectedValueOnce(new Error('Network error'));
      
      fireEvent.press(getByText('Take Photo'));
      
      await waitFor(() => {
        expect(Alert.alert).toHaveBeenCalledWith(
          'Scan Failed',
          'Failed to scan item. Please try again with a clearer image.',
          expect.arrayContaining([{ text: 'OK' }])
        );
      });
    });

    it('should handle HTTP errors', async () => {
      const { getByText } = render(<ScanItemsScreen />);
      
      const mockImageResult = {
        canceled: false,
        assets: [{
          uri: 'test://image.jpg',
          base64: 'mockBase64ImageData',
        }],
      };
      (ImagePicker.launchCameraAsync as jest.Mock).mockResolvedValue(mockImageResult);
      
      // Mock 500 error
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        status: 500,
      });
      
      fireEvent.press(getByText('Take Photo'));
      
      await waitFor(() => {
        expect(Alert.alert).toHaveBeenCalledWith(
          'Scan Failed',
          'Failed to scan item. Please try again with a clearer image.',
          expect.arrayContaining([{ text: 'OK' }])
        );
      });
    });
  });

  describe('Results View', () => {
    it('should show scanning overlay while processing', async () => {
      const { getByText, queryByText } = render(<ScanItemsScreen />);
      
      const mockImageResult = {
        canceled: false,
        assets: [{
          uri: 'test://image.jpg',
          base64: 'mockBase64ImageData',
        }],
      };
      (ImagePicker.launchCameraAsync as jest.Mock).mockResolvedValue(mockImageResult);
      
      // Create a promise we can control
      let resolveResponse: any;
      const responsePromise = new Promise((resolve) => {
        resolveResponse = resolve;
      });
      (global.fetch as jest.Mock).mockReturnValueOnce(responsePromise);
      
      fireEvent.press(getByText('Take Photo'));
      
      // Should show scanning text
      await waitFor(() => {
        expect(getByText('Identifying item...')).toBeTruthy();
        expect(queryByText('Scan Another Item')).toBeNull();
      });
      
      // Resolve the response
      resolveResponse({
        ok: true,
        json: async () => ({ success: true, items: [] }),
      });
    });

    it('should show retry button after scanning completes', async () => {
      const { getByText } = render(<ScanItemsScreen />);
      
      const mockImageResult = {
        canceled: false,
        assets: [{
          uri: 'test://image.jpg',
          base64: 'mockBase64ImageData',
        }],
      };
      (ImagePicker.launchCameraAsync as jest.Mock).mockResolvedValue(mockImageResult);
      
      // Mock response
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ success: true, items: [] }),
      });
      
      fireEvent.press(getByText('Take Photo'));
      
      await waitFor(() => {
        expect(getByText('Scan Another Item')).toBeTruthy();
      });
    });

    it('should reset view when Scan Another Item is pressed', async () => {
      const { getByText, queryByText } = render(<ScanItemsScreen />);
      
      const mockImageResult = {
        canceled: false,
        assets: [{
          uri: 'test://image.jpg',
          base64: 'mockBase64ImageData',
        }],
      };
      (ImagePicker.launchCameraAsync as jest.Mock).mockResolvedValue(mockImageResult);
      
      // Mock response
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ success: true, items: [] }),
      });
      
      fireEvent.press(getByText('Take Photo'));
      
      await waitFor(() => {
        expect(getByText('Scan Another Item')).toBeTruthy();
      });
      
      // Press retry button
      fireEvent.press(getByText('Scan Another Item'));
      
      // Should return to initial view
      expect(getByText('Scan Your Items')).toBeTruthy();
      expect(queryByText('Scan Another Item')).toBeNull();
    });
  });

  describe('Data Transformation', () => {
    it('should use default values when fields are missing', async () => {
      const { getByText } = render(<ScanItemsScreen />);
      
      const mockImageResult = {
        canceled: false,
        assets: [{
          uri: 'test://image.jpg',
          base64: 'mockBase64ImageData',
        }],
      };
      (ImagePicker.launchCameraAsync as jest.Mock).mockResolvedValue(mockImageResult);
      
      // Mock response with minimal data
      const mockScanResponse = {
        success: true,
        items: [{
          name: 'Unknown Product',
          // Missing quantity, unit, category, expiration
        }],
      };
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockScanResponse,
      });
      
      fireEvent.press(getByText('Take Photo'));
      
      await waitFor(() => {
        const navCall = mockRouter.replace.mock.calls[0][0];
        const decodedData = JSON.parse(Buffer.from(navCall.params.data, 'base64').toString());
        
        expect(decodedData[0]).toMatchObject({
          item_name: 'Unknown Product',
          quantity_amount: 1, // Default
          quantity_unit: 'each', // Default
          category: 'Uncategorized', // Default
        });
        
        // Check default expiration is ~7 days from now
        const expDate = new Date(decodedData[0].expected_expiration);
        const daysDiff = Math.round((expDate.getTime() - Date.now()) / (1000 * 60 * 60 * 24));
        expect(daysDiff).toBeGreaterThanOrEqual(6);
        expect(daysDiff).toBeLessThanOrEqual(8);
      });
    });

    it('should use demo user ID when user is not authenticated', async () => {
      // Mock no user
      (useAuth as jest.Mock).mockReturnValue({ user: null });
      
      const { getByText } = render(<ScanItemsScreen />);
      
      const mockImageResult = {
        canceled: false,
        assets: [{
          uri: 'test://image.jpg',
          base64: 'mockBase64ImageData',
        }],
      };
      (ImagePicker.launchCameraAsync as jest.Mock).mockResolvedValue(mockImageResult);
      
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ success: true, items: [] }),
      });
      
      fireEvent.press(getByText('Take Photo'));
      
      await waitFor(() => {
        const fetchCall = (global.fetch as jest.Mock).mock.calls[0];
        const body = JSON.parse(fetchCall[1].body);
        expect(body.user_id).toBe(111); // Demo user ID
      });
    });
  });

  describe('Tips Display', () => {
    it('should display scanning tips', () => {
      const { getByText } = render(<ScanItemsScreen />);
      
      expect(getByText('Tips for best results:')).toBeTruthy();
      expect(getByText('• Focus on the barcode or product label')).toBeTruthy();
      expect(getByText('• Ensure good lighting and sharp focus')).toBeTruthy();
      expect(getByText('• Keep the item flat and steady')).toBeTruthy();
      expect(getByText('• Include nutrition facts for better categorization')).toBeTruthy();
    });
  });
});