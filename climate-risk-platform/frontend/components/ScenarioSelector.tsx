'use client';

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  getScenarioTemplates,
  listScenarios,
  createScenario,
  type ScenarioTemplate,
  type Scenario,
  type ScenarioCreate
} from '@/lib/scenario-api';

interface ScenarioSelectorProps {
  scenarios: Scenario[];
  selectedScenario: Scenario | null;
  onScenarioChange: (scenarioId: string) => void;
  portfolioId: string;
  onRiskCalculated?: () => void;
}

export function ScenarioSelector({
  scenarios: propScenarios,
  selectedScenario,
  onScenarioChange,
  portfolioId,
  onRiskCalculated
}: ScenarioSelectorProps) {
  const [templates, setTemplates] = useState<ScenarioTemplate[]>([]);
  const [scenarios, setScenarios] = useState<Scenario[]>(propScenarios);
  const [isOpen, setIsOpen] = useState(false);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isCalculating, setIsCalculating] = useState(false);

  // Update scenarios when props change
  useEffect(() => {
    setScenarios(propScenarios);
  }, [propScenarios]);

  // Load templates
  useEffect(() => {
    loadTemplates();
  }, []);

  const loadTemplates = async () => {
    try {
      setLoading(true);
      const templatesData = await getScenarioTemplates();
      setTemplates(templatesData);
      setError(null);
    } catch (err) {
      console.error('Error loading templates:', err);
      setError('Failed to load templates');
    } finally {
      setLoading(false);
    }
  };

  const handleScenarioSelect = async (scenarioId: string) => {
    onScenarioChange(scenarioId);
    setIsOpen(false);
    
    // Trigger risk calculation
    if (onRiskCalculated) {
      setIsCalculating(true);
      // Give UI time to update before triggering calculation
      setTimeout(() => {
        onRiskCalculated();
        setIsCalculating(false);
      }, 100);
    }
  };

  return (
    <div className="relative">
      {/* Scenario Selector Dropdown */}
      <div className="flex items-center gap-3">
        <button
          onClick={() => setIsOpen(!isOpen)}
          disabled={isCalculating}
          className="px-4 py-2 bg-slate-800/50 backdrop-blur-sm border border-slate-700/50 rounded-xl hover:bg-slate-700/50 transition-colors flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <span className="text-sm font-medium text-slate-200">
            {selectedScenario ? selectedScenario.name : 'Select Scenario'}
          </span>
          {isCalculating ? (
            <svg className="animate-spin w-4 h-4 text-cyan-400" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
          ) : (
            <svg
              className={`w-4 h-4 text-slate-400 transition-transform ${isOpen ? 'rotate-180' : ''}`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          )}
        </button>

        {/* Create Custom Scenario Button */}
        <button
          onClick={() => setShowCreateModal(true)}
          className="px-4 py-2 bg-emerald-500/20 backdrop-blur-sm border border-emerald-500/50 rounded-xl hover:bg-emerald-500/30 transition-colors text-emerald-300 text-sm font-medium"
        >
          + Custom
        </button>
      </div>

      {/* Dropdown Menu */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.2 }}
            className="absolute top-full left-0 mt-2 w-96 bg-slate-800/95 backdrop-blur-md border border-slate-700/50 rounded-2xl shadow-2xl z-50 overflow-hidden"
          >
            {loading ? (
              <div className="p-4 text-center text-slate-400">Loading scenarios...</div>
            ) : error ? (
              <div className="p-4 text-center text-red-400">{error}</div>
            ) : (
              <div className="max-h-96 overflow-y-auto">
                {/* Templates Section */}
                <div className="p-3 border-b border-slate-700/50">
                  <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
                    Templates
                  </h3>
                  <div className="space-y-1">
                    {templates.map((template, index) => (
                      <button
                        key={index}
                        onClick={() => {
                          // Create scenario from template
                          handleCreateFromTemplate(template);
                          setIsOpen(false);
                        }}
                        className="w-full text-left px-3 py-2 rounded-lg hover:bg-slate-700/50 transition-colors group"
                      >
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="text-sm font-medium text-slate-200 group-hover:text-cyan-300 transition-colors">
                              {template.name}
                            </div>
                            <div className="text-xs text-slate-500 mt-0.5">
                              {template.description}
                            </div>
                          </div>
                          <span className={`text-xs px-2 py-0.5 rounded-full ${
                            template.severity === 'high'
                              ? 'bg-red-500/20 text-red-300'
                              : template.severity === 'medium'
                              ? 'bg-amber-500/20 text-amber-300'
                              : 'bg-emerald-500/20 text-emerald-300'
                          }`}>
                            {template.severity}
                          </span>
                        </div>
                      </button>
                    ))}
                  </div>
                </div>

                {/* Saved Scenarios Section */}
                {scenarios.length > 0 && (
                  <div className="p-3">
                    <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
                      Saved Scenarios
                    </h3>
                    <div className="space-y-1">
                      {scenarios.map((scenario) => (
                        <button
                          key={scenario.id}
                          onClick={() => handleScenarioSelect(scenario.id)}
                          className={`w-full text-left px-3 py-2 rounded-lg transition-colors ${
                            selectedScenario?.id === scenario.id
                              ? 'bg-cyan-500/20 border border-cyan-500/50'
                              : 'hover:bg-slate-700/50'
                          }`}
                        >
                          <div className="flex items-center justify-between">
                            <div className="text-sm font-medium text-slate-200">
                              {scenario.name}
                            </div>
                            <span className={`text-xs px-2 py-0.5 rounded-full ${
                              scenario.severity === 'high'
                                ? 'bg-red-500/20 text-red-300'
                                : scenario.severity === 'medium'
                                ? 'bg-amber-500/20 text-amber-300'
                                : 'bg-emerald-500/20 text-emerald-300'
                            }`}>
                              {scenario.severity}
                            </span>
                          </div>
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Create Custom Scenario Modal */}
      <AnimatePresence>
        {showCreateModal && (
          <CreateScenarioModal
            onClose={() => setShowCreateModal(false)}
            onScenarioCreated={(scenario) => {
              setScenarios([scenario, ...scenarios]);
              handleScenarioSelect(scenario.id);
              setShowCreateModal(false);
            }}
          />
        )}
      </AnimatePresence>
    </div>
  );

  async function handleCreateFromTemplate(template: ScenarioTemplate) {
    try {
      const scenarioData: ScenarioCreate = {
        name: template.name,
        scenario_type: template.scenario_type,
        severity: template.severity,
        time_horizon: template.time_horizon,
        parameters: template.parameters
      };
      const newScenario = await createScenario(scenarioData);
      setScenarios([newScenario, ...scenarios]);
      handleScenarioSelect(newScenario.id);
    } catch (err) {
      console.error('Error creating scenario from template:', err);
      setError('Failed to create scenario');
    }
  }
}

// Create Scenario Modal Component
interface CreateScenarioModalProps {
  onClose: () => void;
  onScenarioCreated: (scenario: Scenario) => void;
}

function CreateScenarioModal({ onClose, onScenarioCreated }: CreateScenarioModalProps) {
  const [formData, setFormData] = useState<ScenarioCreate>({
    name: '',
    scenario_type: 'hurricane',
    severity: 'medium',
    time_horizon: '12m',
    parameters: {}
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setLoading(true);
      setError(null);
      const scenario = await createScenario(formData);
      onScenarioCreated(scenario);
    } catch (err) {
      console.error('Error creating scenario:', err);
      setError('Failed to create scenario');
    } finally {
      setLoading(false);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4"
      onClick={onClose}
    >
      <motion.div
        initial={{ scale: 0.95, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.95, opacity: 0 }}
        className="bg-slate-800/95 backdrop-blur-md border border-slate-700/50 rounded-2xl shadow-2xl max-w-md w-full p-6"
        onClick={(e) => e.stopPropagation()}
      >
        <h2 className="text-xl font-bold text-slate-100 mb-4">Create Custom Scenario</h2>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1">
              Scenario Name
            </label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="w-full px-3 py-2 bg-slate-900/50 border border-slate-700/50 rounded-lg text-slate-200 focus:outline-none focus:ring-2 focus:ring-cyan-500/50"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1">
              Scenario Type
            </label>
            <select
              value={formData.scenario_type}
              onChange={(e) => setFormData({ ...formData, scenario_type: e.target.value })}
              className="w-full px-3 py-2 bg-slate-900/50 border border-slate-700/50 rounded-lg text-slate-200 focus:outline-none focus:ring-2 focus:ring-cyan-500/50"
            >
              <option value="hurricane">Hurricane</option>
              <option value="wildfire">Wildfire</option>
              <option value="drought">Drought</option>
              <option value="heatwave">Heatwave</option>
              <option value="flood">Flood</option>
              <option value="carbon_tax">Carbon Tax</option>
              <option value="emissions_regulation">Emissions Regulation</option>
              <option value="compound">Compound</option>
            </select>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1">
                Severity
              </label>
              <select
                value={formData.severity}
                onChange={(e) => setFormData({ ...formData, severity: e.target.value })}
                className="w-full px-3 py-2 bg-slate-900/50 border border-slate-700/50 rounded-lg text-slate-200 focus:outline-none focus:ring-2 focus:ring-cyan-500/50"
              >
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1">
                Time Horizon
              </label>
              <select
                value={formData.time_horizon}
                onChange={(e) => setFormData({ ...formData, time_horizon: e.target.value })}
                className="w-full px-3 py-2 bg-slate-900/50 border border-slate-700/50 rounded-lg text-slate-200 focus:outline-none focus:ring-2 focus:ring-cyan-500/50"
              >
                <option value="3m">3 months</option>
                <option value="6m">6 months</option>
                <option value="12m">12 months</option>
                <option value="24m">24 months</option>
                <option value="36m">36 months</option>
                <option value="48m">48 months</option>
              </select>
            </div>
          </div>

          {error && (
            <div className="text-sm text-red-400 bg-red-500/10 border border-red-500/20 rounded-lg p-3">
              {error}
            </div>
          )}

          <div className="flex gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 bg-slate-700/50 hover:bg-slate-700 rounded-lg text-slate-300 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="flex-1 px-4 py-2 bg-cyan-500 hover:bg-cyan-600 rounded-lg text-white font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Creating...' : 'Create Scenario'}
            </button>
          </div>
        </form>
      </motion.div>
    </motion.div>
  );
}
