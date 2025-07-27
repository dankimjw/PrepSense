import { useState, useEffect } from 'react';
import { API_BASE_URL } from '../services/api';

export interface ExpiringItem {
  name: string;
  daysLeft: number;
  quantity: number;
  unit: string;
  multiplier: number;
}

export interface TodayImpact {
  items_at_risk: number;
  total_co2e: number;
  supply_chain_multiplier: number;
  economic_value: number;
  driving_equivalent_miles: number;
  items: ExpiringItem[];
}

export interface SupplyChainGuideItem {
  food: string;
  multiplier: number;
  supply_chain_loss_pct: number;
  consumer_loss_pct: number;
  co2e_per_kg: number;
  amplified_co2e: number;
  description: string;
  key_insight: string;
}

export interface WeeklyTrend {
  week: string;
  items_expired: number;
  items_wasted: number;
  items_prevented: number;
  waste_rate: number;
  prevented_co2e: number;
  wasted_co2e: number;
}

export const useSupplyChainImpact = (userId: string) => {
  const [todayImpact, setTodayImpact] = useState<TodayImpact | null>(null);
  const [supplyChainGuide, setSupplyChainGuide] = useState<SupplyChainGuideItem[]>([]);
  const [weeklyTrends, setWeeklyTrends] = useState<WeeklyTrend[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchTodayImpact = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/supply-chain-impact/today-impact/${userId}`);
      if (!response.ok) {
        throw new Error('Failed to fetch today impact');
      }
      const data = await response.json();
      setTodayImpact(data);
    } catch (err) {
      console.error('Error fetching today impact:', err);
      // Set mock data for development
      setTodayImpact({
        items_at_risk: 7,
        total_co2e: 45.3,
        supply_chain_multiplier: 2.2,
        economic_value: 28.50,
        driving_equivalent_miles: 113,
        items: [
          { name: 'Spinach', daysLeft: 1, quantity: 200, unit: 'g', multiplier: 2.4 },
          { name: 'Tomatoes', daysLeft: 2, quantity: 1, unit: 'kg', multiplier: 2.52 },
          { name: 'Bananas', daysLeft: 2, quantity: 6, unit: 'pieces', multiplier: 2.86 },
          { name: 'Lettuce', daysLeft: 1, quantity: 1, unit: 'head', multiplier: 5.7 },
        ]
      });
    }
  };

  const fetchSupplyChainGuide = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/supply-chain-impact/supply-chain-guide`);
      if (!response.ok) {
        throw new Error('Failed to fetch supply chain guide');
      }
      const data = await response.json();
      setSupplyChainGuide(data.multiplier_guide || []);
    } catch (err) {
      console.error('Error fetching supply chain guide:', err);
      // Set mock data for development
      setSupplyChainGuide([
        {
          food: "Lettuce",
          multiplier: 5.7,
          supply_chain_loss_pct: 82.5,
          consumer_loss_pct: 14.4,
          co2e_per_kg: 1.5,
          amplified_co2e: 8.6,
          description: "82.5% lost in supply chain",
          key_insight: "Only 17.5% of lettuce produced reaches consumers"
        },
        {
          food: "Tomatoes",
          multiplier: 2.52,
          supply_chain_loss_pct: 60.3,
          consumer_loss_pct: 9.6,
          co2e_per_kg: 2.09,
          amplified_co2e: 5.3,
          description: "60.3% lost before reaching you",
          key_insight: "For every 1kg wasted, 2.52kg was originally grown"
        },
        {
          food: "Bananas",
          multiplier: 2.86,
          supply_chain_loss_pct: 65.0,
          consumer_loss_pct: 26.0,
          co2e_per_kg: 0.86,
          amplified_co2e: 2.5,
          description: "65% supply chain waste",
          key_insight: "Long supply chains from tropical regions increase waste"
        }
      ]);
    }
  };

  const fetchWeeklyTrends = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/supply-chain-impact/weekly-trends/${userId}`);
      if (!response.ok) {
        throw new Error('Failed to fetch weekly trends');
      }
      const data = await response.json();
      setWeeklyTrends(data.weekly_data || []);
    } catch (err) {
      console.error('Error fetching weekly trends:', err);
      // Set mock data for development
      setWeeklyTrends([
        {
          week: '2025-01-19',
          items_expired: 15,
          items_wasted: 3,
          items_prevented: 12,
          waste_rate: 20.0,
          prevented_co2e: 42.0,
          wasted_co2e: 10.5
        },
        {
          week: '2025-01-12',
          items_expired: 18,
          items_wasted: 5,
          items_prevented: 13,
          waste_rate: 27.8,
          prevented_co2e: 45.5,
          wasted_co2e: 17.5
        }
      ]);
    }
  };

  const refreshData = async () => {
    setLoading(true);
    setError(null);
    try {
      await Promise.all([
        fetchTodayImpact(),
        fetchSupplyChainGuide(),
        fetchWeeklyTrends()
      ]);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (userId) {
      refreshData();
    }
  }, [userId]);

  return {
    todayImpact,
    supplyChainGuide,
    weeklyTrends,
    loading,
    error,
    refreshData
  };
};