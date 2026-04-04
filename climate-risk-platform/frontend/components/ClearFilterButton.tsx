'use client';

/**
 * ClearFilterButton Component
 * 
 * Displays a button to clear active dashboard filters.
 * Only visible when a filter is active.
 */

import React from 'react';
import { X } from 'lucide-react';
import { useDashboardStore } from '@/store/dashboardStore';
import { motion, AnimatePresence } from 'framer-motion';

export function ClearFilterButton() {
  const { filter, clearFilter } = useDashboardStore();
  
  const isFilterActive = filter.holdingId !== null;

  return (
    <AnimatePresence>
      {isFilterActive && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -10 }}
          transition={{ duration: 0.2 }}
          className="fixed top-4 right-4 z-50"
        >
          <button
            onClick={clearFilter}
            className="flex items-center gap-2 px-4 py-2 bg-gray-900/90 backdrop-blur-md border border-gray-700 rounded-xl shadow-lg hover:bg-gray-800 transition-all group"
          >
            <div className="flex items-center gap-2">
              <div className="text-sm">
                <div className="text-gray-400 text-xs">Filtered by:</div>
                <div className="text-white font-semibold">{filter.assetName}</div>
              </div>
              <div className="w-px h-8 bg-gray-700"></div>
              <X className="w-5 h-5 text-gray-400 group-hover:text-red-400 transition-colors" />
            </div>
          </button>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
