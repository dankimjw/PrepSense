import { renderHook, waitFor } from '@testing-library/react-native';
import { useSupplyChainImpact } from '@/hooks/useSupplyChainImpact';
import { mockApiResponses, mockSupplyChainData } from '../helpers/supplyChainMocks';

// Mock fetch
global.fetch = jest.fn();
const mockFetch = fetch as jest.MockedFunction<typeof fetch>;

// Mock API_BASE_URL
jest.mock('@/services/api', () => ({
  API_BASE_URL: 'http://localhost:8000'
}));

describe('useSupplyChainImpact', () => {
  const testUserId = 'test-user-123';

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Successful API Calls', () => {
    beforeEach(() => {
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve(mockApiResponses.todayImpactSuccess)
        } as Response)
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve(mockApiResponses.supplyChainGuideSuccess)
        } as Response)
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve(mockApiResponses.weeklyTrendsSuccess)
        } as Response);
    });

    it('fetches all data on mount', async () => {
      const { result } = renderHook(() => useSupplyChainImpact(testUserId));

      expect(result.current.loading).toBe(true);
      expect(result.current.todayImpact).toBeNull();
      expect(result.current.supplyChainGuide).toEqual([]);
      expect(result.current.weeklyTrends).toEqual([]);

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(result.current.todayImpact).toEqual(mockApiResponses.todayImpactSuccess);
      expect(result.current.supplyChainGuide).toEqual(mockSupplyChainData.supplyChainGuide);
      expect(result.current.weeklyTrends).toEqual(mockSupplyChainData.weeklyTrends);
      expect(result.current.error).toBeNull();
    });

    it('makes correct API calls', async () => {
      renderHook(() => useSupplyChainImpact(testUserId));

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledTimes(3);
      });

      expect(mockFetch).toHaveBeenCalledWith(
        `http://localhost:8000/supply-chain-impact/today-impact/${testUserId}`
      );
      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/supply-chain-impact/supply-chain-guide'
      );
      expect(mockFetch).toHaveBeenCalledWith(
        `http://localhost:8000/supply-chain-impact/weekly-trends/${testUserId}`
      );
    });
  });

  describe('API Error Handling', () => {
    it('falls back to mock data when today impact API fails', async () => {
      mockFetch
        .mockRejectedValueOnce(new Error('Network error'))
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve(mockApiResponses.supplyChainGuideSuccess)
        } as Response)
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve(mockApiResponses.weeklyTrendsSuccess)
        } as Response);

      const { result } = renderHook(() => useSupplyChainImpact(testUserId));

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      // Should have mock data for today impact
      expect(result.current.todayImpact).toBeDefined();
      expect(result.current.todayImpact?.items_at_risk).toBe(7);
      expect(result.current.todayImpact?.items).toHaveLength(4);
    });

    it('falls back to mock data when supply chain guide API fails', async () => {
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve(mockApiResponses.todayImpactSuccess)
        } as Response)
        .mockRejectedValueOnce(new Error('Network error'))
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve(mockApiResponses.weeklyTrendsSuccess)
        } as Response);

      const { result } = renderHook(() => useSupplyChainImpact(testUserId));

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      // Should have mock data for supply chain guide
      expect(result.current.supplyChainGuide).toHaveLength(3);
      expect(result.current.supplyChainGuide[0].food).toBe('Lettuce');
      expect(result.current.supplyChainGuide[0].multiplier).toBe(5.7);
    });

    it('falls back to mock data when weekly trends API fails', async () => {
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve(mockApiResponses.todayImpactSuccess)
        } as Response)
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve(mockApiResponses.supplyChainGuideSuccess)
        } as Response)
        .mockRejectedValueOnce(new Error('Network error'));

      const { result } = renderHook(() => useSupplyChainImpact(testUserId));

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      // Should have mock data for weekly trends
      expect(result.current.weeklyTrends).toHaveLength(2);
      expect(result.current.weeklyTrends[0].week).toBe('2025-01-19');
    });

    it('handles HTTP error responses', async () => {
      mockFetch
        .mockResolvedValueOnce({
          ok: false,
          status: 404,
          json: () => Promise.resolve({ error: 'Not found' })
        } as Response)
        .mockResolvedValueOnce({
          ok: false,
          status: 500,
          json: () => Promise.resolve({ error: 'Server error' })
        } as Response)
        .mockResolvedValueOnce({
          ok: false,
          status: 400,
          json: () => Promise.resolve({ error: 'Bad request' })
        } as Response);

      const { result } = renderHook(() => useSupplyChainImpact(testUserId));

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      // Should fall back to mock data for all endpoints
      expect(result.current.todayImpact).toBeDefined();
      expect(result.current.supplyChainGuide).toHaveLength(3);
      expect(result.current.weeklyTrends).toHaveLength(2);
    });
  });

  describe('Refresh Data Function', () => {
    it('provides refreshData function', async () => {
      mockFetch
        .mockResolvedValue({
          ok: true,
          json: () => Promise.resolve(mockApiResponses.todayImpactSuccess)
        } as Response);

      const { result } = renderHook(() => useSupplyChainImpact(testUserId));

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(typeof result.current.refreshData).toBe('function');
    });

    it('refreshData re-fetches all data', async () => {
      mockFetch
        .mockResolvedValue({
          ok: true,
          json: () => Promise.resolve(mockApiResponses.todayImpactSuccess)
        } as Response);

      const { result } = renderHook(() => useSupplyChainImpact(testUserId));

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      // Clear previous calls
      mockFetch.mockClear();

      // Call refreshData
      await result.current.refreshData();

      expect(mockFetch).toHaveBeenCalledTimes(3);
    });
  });

  describe('Loading States', () => {
    it('starts with loading true', () => {
      mockFetch.mockImplementation(() => new Promise(() => {})); // Never resolves

      const { result } = renderHook(() => useSupplyChainImpact(testUserId));

      expect(result.current.loading).toBe(true);
      expect(result.current.todayImpact).toBeNull();
      expect(result.current.supplyChainGuide).toEqual([]);
      expect(result.current.weeklyTrends).toEqual([]);
    });

    it('sets loading false after all requests complete', async () => {
      mockFetch
        .mockResolvedValue({
          ok: true,
          json: () => Promise.resolve({})
        } as Response);

      const { result } = renderHook(() => useSupplyChainImpact(testUserId));

      expect(result.current.loading).toBe(true);

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });
    });
  });

  describe('User ID Changes', () => {
    it('refetches data when userId changes', async () => {
      mockFetch
        .mockResolvedValue({
          ok: true,
          json: () => Promise.resolve(mockApiResponses.todayImpactSuccess)
        } as Response);

      const { result, rerender } = renderHook(
        ({ userId }) => useSupplyChainImpact(userId),
        { initialProps: { userId: 'user1' } }
      );

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(mockFetch).toHaveBeenCalledTimes(3);
      mockFetch.mockClear();

      // Change userId
      rerender({ userId: 'user2' });

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledTimes(3);
      });

      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/supply-chain-impact/today-impact/user2'
      );
      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/supply-chain-impact/weekly-trends/user2'
      );
    });

    it('does not fetch when userId is empty', () => {
      const { result } = renderHook(() => useSupplyChainImpact(''));

      expect(result.current.loading).toBe(true);
      expect(mockFetch).not.toHaveBeenCalled();
    });
  });

  describe('Data Structure Validation', () => {
    it('handles missing multiplier_guide in supply chain response', async () => {
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve(mockApiResponses.todayImpactSuccess)
        } as Response)
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({}) // Missing multiplier_guide
        } as Response)
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve(mockApiResponses.weeklyTrendsSuccess)
        } as Response);

      const { result } = renderHook(() => useSupplyChainImpact(testUserId));

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(result.current.supplyChainGuide).toEqual([]);
    });

    it('handles missing weekly_data in trends response', async () => {
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve(mockApiResponses.todayImpactSuccess)
        } as Response)
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve(mockApiResponses.supplyChainGuideSuccess)
        } as Response)
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({}) // Missing weekly_data
        } as Response);

      const { result } = renderHook(() => useSupplyChainImpact(testUserId));

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(result.current.weeklyTrends).toEqual([]);
    });
  });
});