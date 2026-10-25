import React from 'react';
import { EyeOff, KeyRound, Flame, FileCheck, RefreshCw } from 'lucide-react';
import { DashboardStats } from '../services/api';

interface MetricBarProps {
  stats: DashboardStats | null;
  isLoading: boolean;
  onRefresh: () => void;
}

export const MetricBar: React.FC<MetricBarProps> = ({
  stats,
  isLoading,
  onRefresh,
}) => {
  const cards = [
    {
      title: 'Screenshots Redacted',
      value: stats?.total_screenshots_redacted ?? 0,
      icon: EyeOff,
      accent: 'cyan',
      glow: 'shadow-cyan-500/10 border-cyan-500/20 text-cyan-400',
      label: 'Zero-Leak Pixel DLP',
    },
    {
      title: 'Active Honey-Tokens',
      value: stats?.active_honey_tokens ?? 0,
      icon: KeyRound,
      accent: 'amber',
      glow: 'shadow-amber-500/10 border-amber-500/20 text-amber-400',
      label: 'Synthetic Decoys Seeded',
    },
    {
      title: 'Circuit-Breaker Blocks',
      value: stats?.blocked_scavenge_attempts ?? 0,
      icon: Flame,
      accent: 'rose',
      glow: 'shadow-rose-500/10 border-rose-500/20 text-rose-400',
      label: 'Scavenge Attacks Halted',
    },
    {
      title: 'Skill Trace Audits',
      value: stats?.airlock_audits ?? 0,
      icon: FileCheck,
      accent: 'emerald',
      glow: 'shadow-emerald-500/10 border-emerald-500/20 text-emerald-400',
      label: 'Pre-Commit & Trace Clean',
    },
  ];

  return (
    <div className="mb-6">
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-xs font-mono font-semibold tracking-wider text-slate-400 uppercase flex items-center space-x-2">
          <span>Global Telemetry Overview</span>
          <span className="h-1.5 w-1.5 rounded-full bg-cyan-400 animate-ping" />
        </h2>
        <button
          onClick={onRefresh}
          disabled={isLoading}
          className="text-xs text-slate-400 hover:text-cyan-400 flex items-center space-x-1.5 transition-colors disabled:opacity-50"
        >
          <RefreshCw className={`h-3 w-3 ${isLoading ? 'animate-spin text-cyan-400' : ''}`} />
          <span>Sync Telemetry</span>
        </button>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {cards.map((card, idx) => {
          const Icon = card.icon;
          return (
            <div
              key={idx}
              className={`relative overflow-hidden rounded-xl bg-slate-900/80 p-4 border transition-all hover:translate-y-[-2px] hover:shadow-lg ${card.glow}`}
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs font-medium text-slate-400">{card.title}</p>
                  <p className="mt-1 text-2xl font-bold font-mono tracking-tight text-white">
                    {card.value}
                  </p>
                </div>
                <div className={`p-2.5 rounded-lg bg-slate-800/80 ${card.glow.split(' ')[2]}`}>
                  <Icon className="h-5 w-5" />
                </div>
              </div>
              <div className="mt-2.5 flex items-center space-x-1 text-[11px] text-slate-400 font-mono">
                <span className="text-slate-500">DEFENSE:</span>
                <span>{card.label}</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
