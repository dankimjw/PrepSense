// services/api.ts - API service for PrepSense

const API_BASE_URL = 'http://localhost:8001/api/v1';

export interface PantryItem {
  id: string;
  item_name: string;
  quantity_amount: number;
  quantity_unit: string;
  expected_expiration: string;
  addedDate?: string;
  category?: string;
  [key: string]: any; // Allow additional properties from the API
}

export const fetchPantryItems = async (userId: number): Promise<PantryItem[]> => {
  try {
    const response = await fetch(`${API_BASE_URL}/pantry/user/${userId}/items`);
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Error fetching pantry items: ${response.statusText}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('Error fetching pantry items:', error);
    throw error;
  }
};
