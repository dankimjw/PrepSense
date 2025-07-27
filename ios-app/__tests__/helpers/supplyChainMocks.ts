import { TodayImpact, SupplyChainGuideItem, WeeklyTrend, ExpiringItem } from '../../hooks/useSupplyChainImpact';

// Mock data helpers for supply chain impact tests
export const createMockExpiringItem = (overrides: Partial<ExpiringItem> = {}): ExpiringItem => ({
  name: 'Test Item',
  daysLeft: 2,
  quantity: 1,
  unit: 'kg',
  multiplier: 2.5,
  ...overrides
});

export const createMockTodayImpact = (overrides: Partial<TodayImpact> = {}): TodayImpact => ({
  items_at_risk: 5,
  total_co2e: 23.4,
  supply_chain_multiplier: 2.2,
  economic_value: 15.80,
  driving_equivalent_miles: 58,
  items: [
    createMockExpiringItem({ name: 'Lettuce', daysLeft: 1, quantity: 1, unit: 'head', multiplier: 5.7 }),
    createMockExpiringItem({ name: 'Tomatoes', daysLeft: 2, quantity: 500, unit: 'g', multiplier: 2.52 }),
    createMockExpiringItem({ name: 'Bananas', daysLeft: 1, quantity: 3, unit: 'pieces', multiplier: 2.86 })
  ],
  ...overrides
});

export const createMockSupplyChainGuideItem = (overrides: Partial<SupplyChainGuideItem> = {}): SupplyChainGuideItem => ({
  food: 'Test Food',
  multiplier: 2.5,
  supply_chain_loss_pct: 60.0,
  consumer_loss_pct: 15.0,
  co2e_per_kg: 2.0,
  amplified_co2e: 5.0,
  description: '60% lost in supply chain',
  key_insight: 'High supply chain waste',
  ...overrides
});

export const createMockWeeklyTrend = (overrides: Partial<WeeklyTrend> = {}): WeeklyTrend => ({
  week: '2025-01-20',
  items_expired: 10,
  items_wasted: 2,
  items_prevented: 8,
  waste_rate: 20.0,
  prevented_co2e: 25.5,
  wasted_co2e: 6.4,
  ...overrides
});

// Complete mock data sets
export const mockSupplyChainData = {
  todayImpact: createMockTodayImpact(),
  supplyChainGuide: [
    createMockSupplyChainGuideItem({
      food: 'Lettuce',
      multiplier: 5.7,
      supply_chain_loss_pct: 82.5,
      consumer_loss_pct: 14.4,
      co2e_per_kg: 1.5,
      amplified_co2e: 8.6,
      description: '82.5% lost in supply chain',
      key_insight: 'Only 17.5% of lettuce produced reaches consumers'
    }),
    createMockSupplyChainGuideItem({
      food: 'Tomatoes',
      multiplier: 2.52,
      supply_chain_loss_pct: 60.3,
      consumer_loss_pct: 9.6,
      co2e_per_kg: 2.09,
      amplified_co2e: 5.3,
      description: '60.3% lost before reaching you',
      key_insight: 'For every 1kg wasted, 2.52kg was originally grown'
    }),
    createMockSupplyChainGuideItem({
      food: 'Bananas',
      multiplier: 2.86,
      supply_chain_loss_pct: 65.0,
      consumer_loss_pct: 26.0,
      co2e_per_kg: 0.86,
      amplified_co2e: 2.5,
      description: '65% supply chain waste',
      key_insight: 'Long supply chains from tropical regions increase waste'
    })
  ],
  weeklyTrends: [
    createMockWeeklyTrend({
      week: '2025-01-20',
      items_expired: 15,
      items_wasted: 3,
      items_prevented: 12,
      waste_rate: 20.0,
      prevented_co2e: 42.0,
      wasted_co2e: 10.5
    }),
    createMockWeeklyTrend({
      week: '2025-01-13',
      items_expired: 18,
      items_wasted: 5,
      items_prevented: 13,
      waste_rate: 27.8,
      prevented_co2e: 45.5,
      wasted_co2e: 17.5
    })
  ]
};

// API Mock responses
export const mockFetchResponse = (data: any, ok: boolean = true, status: number = 200) => {
  return Promise.resolve({
    ok,
    status,
    json: () => Promise.resolve(data)
  } as Response);
};

export const mockApiResponses = {
  todayImpactSuccess: mockSupplyChainData.todayImpact,
  supplyChainGuideSuccess: { multiplier_guide: mockSupplyChainData.supplyChainGuide },
  weeklyTrendsSuccess: { weekly_data: mockSupplyChainData.weeklyTrends },
  todayImpactError: mockFetchResponse({ error: 'Failed to fetch today impact' }, false, 500),
  supplyChainGuideError: mockFetchResponse({ error: 'Failed to fetch guide' }, false, 500),
  weeklyTrendsError: mockFetchResponse({ error: 'Failed to fetch trends' }, false, 500)
};

// Empty/edge case data
export const emptySupplyChainData = {
  todayImpact: createMockTodayImpact({
    items_at_risk: 0,
    total_co2e: 0,
    supply_chain_multiplier: 0,
    economic_value: 0,
    driving_equivalent_miles: 0,
    items: []
  }),
  supplyChainGuide: [],
  weeklyTrends: []
};

// High impact scenario for testing
export const highImpactScenario = {
  todayImpact: createMockTodayImpact({
    items_at_risk: 15,
    total_co2e: 125.8,
    supply_chain_multiplier: 4.2,
    economic_value: 85.50,
    driving_equivalent_miles: 314,
    items: [
      createMockExpiringItem({ name: 'Lettuce', daysLeft: 0, quantity: 2, unit: 'heads', multiplier: 5.7 }),
      createMockExpiringItem({ name: 'Avocados', daysLeft: 1, quantity: 6, unit: 'pieces', multiplier: 3.8 }),
      createMockExpiringItem({ name: 'Berries', daysLeft: 0, quantity: 500, unit: 'g', multiplier: 4.1 }),
      createMockExpiringItem({ name: 'Tomatoes', daysLeft: 1, quantity: 1, unit: 'kg', multiplier: 2.52 })
    ]
  })
};

// Loading states
export const loadingState = {
  todayImpact: null,
  supplyChainGuide: [],
  weeklyTrends: [],
  loading: true,
  error: null
};

// Error states
export const errorState = {
  todayImpact: null,
  supplyChainGuide: [],
  weeklyTrends: [],
  loading: false,
  error: 'Failed to fetch supply chain data'
};