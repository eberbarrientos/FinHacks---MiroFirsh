'use client';

/**
 * MiroFishNarrativePanel - Displays cascade simulation narrative and impact summary
 * 
 * Features:
 * - Formatted narrative text with entity highlighting
 * - Cascade impact summary (propagated loss, affected entities)
 * - Loading indicator during simulation
 * - Error handling for failed simulations
 */

import React, { useMemo } from 'react';
import { Loader2, AlertCircle, TrendingUp, Users } from 'lucide-react';

interface MiroFishNarrativePanelProps {
  status: 'idle' | 'loading' | 'completed' | 'failed' | 'unavailable';
  narrative?: string;
  propagatedLoss?: number;
  affectedEntityCount?: number;
  error?: string;
  estimatedTime?: number;
  className?: string;
}

export function MiroFishNarrativePanel({
  status,
  narrative,
  propagatedLoss,
  affectedEntityCount,
  error,
  estimatedTime = 60,
  className = '',
}: MiroFishNarrativePanelProps) {
  // Highlight entities in narrative (words in quotes or capitalized phrases)
  const highlightedNarrative = useMemo(() => {
    if (!narrative) return null;

    // Split by quotes and capitalize patterns
    const parts = narrative.split(/(".*?"|[A-Z][a-z]+(?: [A-Z][a-z]+)*)/g);
    
    return parts.map((part, index) => {
      // Check if it's a quoted string or capitalized phrase
      if (part.startsWith('"') || /^[A-Z][a-z]+(?: [A-Z][a-z]+)*$/.test(part)) {
        return (
          <span
            key={index}
            className="text-cyan-400 font-semibold"
          >
            {part}
          </span>
        );
      }
      return <span key={index}>{part}</span>;
    });
  }, [narrative]);

  // Format currency
  const formatCurrency = (value: number) => {
    if (value >= 1_000_000_000) {
      return `$${(value / 1_000_000_000).toFixed(2)}B`;
    } else if (value >= 1_000_000) {
      return `$${(value / 1_000_000).toFixed(2)}M`;
    } else if (value >= 1_000) {
      return `$${(value / 1_000).toFixed(2)}K`;
    }
    return `$${value.toFixed(2)}`;
  };

  return (
    <div className={`rounded-2xl bg-slate-900/50 backdrop-blur-sm border border-slate-700/50 p-6 ${className}`}>
      <h3 className="text-lg font-semibold text-white mb-4">Cascade Analysis</h3>

      {/* Loading State */}
      {status === 'loading' && (
        <div className="flex flex-col items-center justify-center py-12 space-y-4">
          <Loader2 className="w-12 h-12 text-cyan-500 animate-spin" />
          <div className="text-center">
            <p className="text-white font-medium">Running cascade simulation...</p>
            <p className="text-sm text-slate-400 mt-2">
              Estimated completion time: {estimatedTime} seconds
            </p>
          </div>
          <div className="w-full max-w-md bg-slate-800/50 rounded-full h-2 overflow-hidden">
            <div className="h-full bg-gradient-to-r from-cyan-500 to-blue-500 animate-pulse" style={{ width: '60%' }}></div>
          </div>
        </div>
      )}

      {/* Error State */}
      {status === 'failed' && (
        <div className="flex items-start gap-3 p-4 rounded-xl bg-red-500/10 border border-red-500/30">
          <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-red-400 font-medium">Simulation Failed</p>
            <p className="text-sm text-red-300/80 mt-1">{error || 'An error occurred during cascade simulation'}</p>
          </div>
        </div>
      )}

      {/* Unavailable State */}
      {status === 'unavailable' && (
        <div className="flex items-start gap-3 p-4 rounded-xl bg-amber-500/10 border border-amber-500/30">
          <AlertCircle className="w-5 h-5 text-amber-400 flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-amber-400 font-medium">Cascade Analysis Unavailable</p>
            <p className="text-sm text-amber-300/80 mt-1">
              {error || 'Cascade analysis unavailable - showing direct risk only'}
            </p>
          </div>
        </div>
      )}

      {/* Idle State */}
      {status === 'idle' && (
        <div className="flex items-center justify-center py-12 text-slate-400">
          <p>Run risk calculation to trigger cascade simulation</p>
        </div>
      )}

      {/* Completed State */}
      {status === 'completed' && (
        <div className="space-y-6">
          {/* Impact Summary */}
          {(propagatedLoss !== undefined || affectedEntityCount !== undefined) && (
            <div className="grid grid-cols-2 gap-4">
              {propagatedLoss !== undefined && (
                <div className="p-4 rounded-xl bg-slate-800/50 border border-slate-700/50">
                  <div className="flex items-center gap-2 text-slate-400 text-sm mb-2">
                    <TrendingUp className="w-4 h-4" />
                    <span>Propagated Loss</span>
                  </div>
                  <p className="text-2xl font-bold text-red-400">
                    {formatCurrency(propagatedLoss)}
                  </p>
                </div>
              )}
              
              {affectedEntityCount !== undefined && (
                <div className="p-4 rounded-xl bg-slate-800/50 border border-slate-700/50">
                  <div className="flex items-center gap-2 text-slate-400 text-sm mb-2">
                    <Users className="w-4 h-4" />
                    <span>Affected Entities</span>
                  </div>
                  <p className="text-2xl font-bold text-amber-400">
                    {affectedEntityCount}
                  </p>
                </div>
              )}
            </div>
          )}

          {/* Narrative */}
          {narrative && (
            <div className="space-y-3">
              <h4 className="text-sm font-semibold text-slate-300 uppercase tracking-wide">
                Dependency Narrative
              </h4>
              <div className="p-4 rounded-xl bg-slate-950/50 border border-slate-700/30">
                <p className="text-slate-200 leading-relaxed whitespace-pre-wrap">
                  {highlightedNarrative}
                </p>
              </div>
            </div>
          )}

          {/* Insights */}
          <div className="p-4 rounded-xl bg-cyan-500/10 border border-cyan-500/30">
            <p className="text-sm text-cyan-300">
              <span className="font-semibold">Key Insight:</span> The cascade simulation reveals
              second-order effects that amplify direct climate risks through dependency networks.
              Consider these propagation paths when developing mitigation strategies.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
