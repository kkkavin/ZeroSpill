import React, { useState, useEffect, useCallback } from 'react';
import { Header } from './components/Header';
import { MetricBar } from './components/MetricBar';
import { PixelShieldTab } from './components/PixelShieldTab';
import { HoneyTrapTab } from './components/HoneyTrapTab';
import { AirlockTab } from './components/AirlockTab';
import { AgentHookTab } from './components/AgentHookTab';
import { api, DashboardStats } from './services/api';
import { Shield, Activity, AlertTriangle, CheckCircle2 } from 'lucide-react';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'pixel' | 'honey' | 'airlock' | 'agent'>('pixel');
  const [isBackendOnline, setIsBackendOnline] = useState<boolean>(false);
  const [isProductionMode, setIsProductionMode] = useState<boolean>(true); // Default to Production Mode
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loadingStats, setLoadingStats] = useState<boolean>(false);
  const [isResetting, setIsResetting] = useState<boolean>(false);

  const fetchStats = useCallback(async () => {
    setLoadingStats(true);
    try {
      const data = await api.getDashboardStats();
      setStats(data);
      setIsBackendOnline(true);
    } catch {
      setIsBackendOnline(false);
    } finally {
      setLoadingStats(false);
    }
  }, []);

  const handleResetDb = async () => {
    if (!window.confirm('Reset ZeroSpill database to a 100% clean slate? All logs and decoys will be cleared.')) {
      return;
    }
    setIsResetting(true);
    try {
      await api.resetDatabase();
      await fetchStats();
    } catch (err) {
      console.error('Failed to reset DB:', err);
    } finally {
      setIsResetting(false);
    }
  };

  useEffect(() => {
    fetchStats();
    const interval = setInterval(fetchStats, 10000);
    return () => clearInterval(interval);
  }, [fetchStats]);

  return (
    <div className="min-h-screen bg-[#080c14] text-slate-100 flex flex-col selection:bg-cyan-500/20">
      {/* Background Cyber Grid Accent */}
      <div className="fixed inset-0 pointer-events-none opacity-20 bg-[radial-gradient(#1e293b_1px,transparent_1px)] [background-size:16px_16px]" />

      <Header
        isBackendOnline={isBackendOnline}
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        isProductionMode={isProductionMode}
        setIsProductionMode={setIsProductionMode}
        onResetDb={handleResetDb}
        isResetting={isResetting}
      />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 relative z-10">
        <MetricBar
          stats={stats}
          isLoading={loadingStats}
          onRefresh={fetchStats}
        />

        {/* Tab Views */}
        <div className="mt-4">
          {activeTab === 'pixel' && (
            <PixelShieldTab
              onScanCompleted={fetchStats}
              isProductionMode={isProductionMode}
            />
          )}
          {activeTab === 'honey' && (
            <HoneyTrapTab
              onIncidentTriggered={fetchStats}
              isProductionMode={isProductionMode}
            />
          )}
          {activeTab === 'airlock' && (
            <AirlockTab onScanCompleted={fetchStats} />
          )}
          {activeTab === 'agent' && (
            <AgentHookTab />
          )}
        </div>

        {/* Live Security Event Stream Drawer */}
        {stats && stats.recent_events && stats.recent_events.length > 0 && (
          <div className="mt-8 bg-slate-900/80 rounded-2xl p-5 border border-slate-800 backdrop-blur-sm">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center space-x-2">
                <Activity className="h-4 w-4 text-cyan-400" />
                <h4 className="text-xs font-mono font-bold uppercase text-slate-300 tracking-wider">
                  Live Security Incident Audit Log (SQLite Stream)
                </h4>
              </div>
              <span className="text-[11px] font-mono text-slate-500">
                Last {stats.recent_events.length} security events
              </span>
            </div>

            <div className="space-y-2">
              {stats.recent_events.map((ev) => (
                <div
                  key={ev.id}
                  className="flex flex-col sm:flex-row sm:items-center justify-between p-2.5 rounded-lg bg-slate-950/70 border border-slate-800/80 text-xs font-mono gap-2 hover:border-slate-700 transition-colors"
                >
                  <div className="flex items-center space-x-2 overflow-hidden">
                    {ev.blocked ? (
                      <AlertTriangle className="h-3.5 w-3.5 text-rose-400 shrink-0" />
                    ) : (
                      <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400 shrink-0" />
                    )}
                    <span className="font-bold text-slate-200">{ev.title}</span>
                    <span className="text-slate-500 hidden md:inline">&bull;</span>
                    <span className="text-slate-400 truncate">{ev.details}</span>
                  </div>

                  <div className="flex items-center space-x-2 shrink-0">
                    <span
                      className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                        ev.severity === 'CRITICAL'
                          ? 'bg-rose-500/10 text-rose-400 border border-rose-500/30'
                          : ev.severity === 'HIGH'
                          ? 'bg-amber-500/10 text-amber-400 border border-amber-500/30'
                          : 'bg-slate-800 text-slate-400'
                      }`}
                    >
                      {ev.severity}
                    </span>
                    <span className="text-[10px] text-slate-500">
                      {new Date(ev.timestamp).toLocaleTimeString()}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800/80 bg-slate-950/60 py-6 text-center text-xs text-slate-500 relative z-10 font-mono">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-2">
          <div className="flex items-center space-x-2 text-slate-400">
            <Shield className="h-4 w-4 text-cyan-400" />
            <span className="font-bold text-slate-300">ZeroSpill v2.0 Neural Engine</span>
            <span>&mdash; Open-Source AI Agent Security</span>
          </div>
          <div className="flex items-center space-x-3">
            <span className="px-2 py-0.5 rounded bg-slate-900 border border-slate-800 text-slate-400">
              {isProductionMode ? 'Mode: Production Strict' : 'Mode: Sandbox Interactive'}
            </span>
            <span>MIT Licensed</span>
          </div>
        </div>
      </footer>
    </div>
  );
};
