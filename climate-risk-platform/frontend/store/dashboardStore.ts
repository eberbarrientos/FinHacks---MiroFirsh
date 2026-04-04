/**
 * Dashboard state management with Zustand
 * Manages filter state for map interactions and dashboard filtering
 */

import { create } from 'zustand';

export interface DashboardFilter {
  holdingId: string | null;
  assetName: string | null;
  issuerName: string | null;
}

interface DashboardState {
  // Filter state
  filter: DashboardFilter;
  
  // Actions
  setFilter: (filter: DashboardFilter) => void;
  clearFilter: () => void;
  filterByHolding: (holdingId: string, assetName: string, issuerName: string) => void;
}

const initialFilter: DashboardFilter = {
  holdingId: null,
  assetName: null,
  issuerName: null,
};

export const useDashboardStore = create<DashboardState>((set) => ({
  filter: initialFilter,
  
  setFilter: (filter) => set({ filter }),
  
  clearFilter: () => set({ filter: initialFilter }),
  
  filterByHolding: (holdingId, assetName, issuerName) =>
    set({
      filter: {
        holdingId,
        assetName,
        issuerName,
      },
    }),
}));
