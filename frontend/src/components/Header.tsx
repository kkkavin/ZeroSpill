import React from 'react';
import {
  Shield,
  ShieldAlert,
  Cpu,
  Terminal,
  GitBranch,
  RotateCcw,
  ToggleLeft,
  ToggleRight,
} from 'lucide-react';

interface HeaderProps {
  isBackendOnline: boolean;
  activeTab: 'pixel' | 'honey' | 'airlock' | 'agent';
  setActiveTab: (tab: 'pixel' | 'honey' | 'airlock' | 'agent') => void;
  isProductionMode: boolean;
  setIsProductionMode: (prod: boolean) => void;
  onResetDb: () => void;
  isResetting: boolean;
}

export const Header: React.FC<HeaderProps> = ({
  isBackendOnline,
  activeTab,
  setActiveTab,
  isProductionMode,
  setIsProductionMode,
  onResetDb,
  isResetting,
}) => {
  return (
    <header className="border-b border-slate-800/80 bg-slate-950/80 backdrop-blur-md sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16 gap-2">
          {/* Logo & Brand */}
          <div className="flex items-center space-x-3 shrink-0">
            <div className="h-10 w-10 rounded-xl bg-gradient-to-tr from-cyan-600 via-indigo-600 to-rose-500 p-0.5 shadow-lg shadow-cyan-500/20">
              <div className="h-full w-full bg-slate-950 rounded-[10px] flex items-center justify-center">
                <Shield className="h-5 w-5 text-cyan-400" />
              </div>
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="text-xl font-bold tracking-tight text-white font-mono">
                  Zero<span className="text-cyan-400">Spill</span>
                </span>
                <span className="px-1.5 py-0.5 text-[10px] uppercase font-mono font-semibold rounded bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                  v2.0 Neural
                </span>
              </div>
              <p className="text-xs text-slate-400 hidden sm:block">
                Autonomous AI Coding Agent Guardrail & Token Defense
              </p>
            </div>
          </div>

          {/* Navigation Tabs */}
          <div className="flex items-center space-x-1 sm:space-x-1.5 bg-slate-900/90 p-1 rounded-xl border border-slate-800 overflow-x-auto">
            <button
              onClick={() => setActiveTab('pixel')}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs sm:text-sm font-medium transition-all shrink-0 ${
                activeTab === 'pixel'
                  ? 'bg-gradient-to-r from-cyan-500/20 to-blue-500/20 text-cyan-300 border border-cyan-500/30 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
              }`}
            >
              <Cpu className="h-4 w-4" />
              <span>Pixel-Shield</span>
            </button>
            <button
              onClick={() => setActiveTab('honey')}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs sm:text-sm font-medium transition-all shrink-0 ${
                activeTab === 'honey'
                  ? 'bg-gradient-to-r from-rose-500/20 to-amber-500/20 text-rose-300 border border-rose-500/30 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
              }`}
            >
              <ShieldAlert className="h-4 w-4" />
              <span>Honey-Token Trap</span>
            </button>
            <button
              onClick={() => setActiveTab('airlock')}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs sm:text-sm font-medium transition-all shrink-0 ${
                activeTab === 'airlock'
                  ? 'bg-gradient-to-r from-emerald-500/20 to-teal-500/20 text-emerald-300 border border-emerald-500/30 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
              }`}
            >
              <Terminal className="h-4 w-4" />
              <span>Skill Trace Airlock</span>
            </button>
            <button
              onClick={() => setActiveTab('agent')}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs sm:text-sm font-medium transition-all shrink-0 ${
                activeTab === 'agent'
                  ? 'bg-gradient-to-r from-purple-500/20 to-indigo-500/20 text-purple-300 border border-purple-500/30 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
              }`}
            >
              <GitBranch className="h-4 w-4" />
              <span>Agent & Git Hook</span>
            </button>
          </div>

          {/* Right Controls: Mode Switch, Reset DB, Status Badge */}
          <div className="flex items-center space-x-2 sm:space-x-3 shrink-0">
            {/* Production vs Sandbox Mode Switch */}
            <button
              onClick={() => setIsProductionMode(!isProductionMode)}
              className={`flex items-center space-x-1.5 px-2.5 py-1.5 rounded-lg text-xs font-mono font-medium border transition-all ${
                isProductionMode
                  ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30 hover:bg-emerald-500/20'
                  : 'bg-amber-500/10 text-amber-400 border-amber-500/30 hover:bg-amber-500/20'
              }`}
              title={
                isProductionMode
                  ? 'Production Mode Active: Live OCR only, synthetic presets hidden'
                  : 'Sandbox Mode Active: Demo buttons & attack presets enabled'
              }
            >
              {isProductionMode ? (
                <>
                  <ToggleRight className="h-4 w-4 text-emerald-400" />
                  <span className="hidden sm:inline">PROD MODE</span>
                </>
              ) : (
                <>
                  <ToggleLeft className="h-4 w-4 text-amber-400" />
                  <span className="hidden sm:inline">SANDBOX</span>
                </>
              )}
            </button>

            {/* Reset DB Button */}
            <button
              onClick={onResetDb}
              disabled={isResetting}
              className="p-1.5 sm:px-2.5 sm:py-1.5 rounded-lg text-xs font-mono font-medium bg-slate-900 hover:bg-rose-950/40 text-slate-400 hover:text-rose-400 border border-slate-800 hover:border-rose-500/30 transition-all flex items-center space-x-1 disabled:opacity-50"
              title="Reset SQLite database to 100% clean slate"
            >
              <RotateCcw className={`h-3.5 w-3.5 ${isResetting ? 'animate-spin text-rose-400' : ''}`} />
              <span className="hidden md:inline">Reset DB</span>
            </button>

            {/* Status Badge */}
            <div
              className={`flex items-center space-x-1.5 px-2.5 py-1 rounded-full text-xs font-mono font-medium border ${
                isBackendOnline
                  ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                  : 'bg-rose-500/10 text-rose-400 border-rose-500/30'
              }`}
            >
              <span
                className={`h-2 w-2 rounded-full ${
                  isBackendOnline ? 'bg-emerald-400 animate-pulse' : 'bg-rose-400'
                }`}
              />
              <span className="hidden lg:inline">
                {isBackendOnline ? 'V2.0 LIVE' : 'OFFLINE'}
              </span>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};
