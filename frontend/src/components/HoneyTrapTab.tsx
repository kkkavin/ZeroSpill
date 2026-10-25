import React, { useState, useEffect } from 'react';
import {
  ShieldAlert,
  Key,
  Terminal,
  Copy,
  Check,
  Flame,
  AlertOctagon,
  CheckCircle,
  RefreshCw,
  Zap,
  FileCode2,
  Radio,
} from 'lucide-react';
import { api, HoneyToken, InspectCommandResponse, PlantDecoyResponse } from '../services/api';

interface HoneyTrapTabProps {
  onIncidentTriggered: () => void;
  isProductionMode: boolean;
}

export const HoneyTrapTab: React.FC<HoneyTrapTabProps> = ({
  onIncidentTriggered,
  isProductionMode,
}) => {
  const [tokens, setTokens] = useState<HoneyToken[]>([]);
  const [loadingTokens, setLoadingTokens] = useState<boolean>(false);
  const [commandInput, setCommandInput] = useState<string>('cat .env.production');
  const [inspecting, setInspecting] = useState<boolean>(false);
  const [result, setResult] = useState<InspectCommandResponse | null>(null);
  const [copiedId, setCopiedId] = useState<number | null>(null);
  const [plantedDecoy, setPlantedDecoy] = useState<PlantDecoyResponse | null>(null);
  const [planting, setPlanting] = useState<boolean>(false);

  const fetchTokens = async () => {
    setLoadingTokens(true);
    try {
      const data = await api.getHoneyTokens();
      setTokens(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoadingTokens(false);
    }
  };

  const handleDeployTokens = async () => {
    setLoadingTokens(true);
    try {
      const res = await api.deployHoneyTokens();
      setTokens(res.tokens);
    } catch (err) {
      console.error(err);
    } finally {
      setLoadingTokens(false);
    }
  };

  const handlePlantFile = async () => {
    setPlanting(true);
    try {
      const res = await api.plantDecoyFile();
      setPlantedDecoy(res);
      await fetchTokens();
    } catch (err) {
      console.error(err);
    } finally {
      setPlanting(false);
    }
  };

  const handleTestCanary = async () => {
    setInspecting(true);
    setResult(null);
    try {
      const tokenId = tokens[0]?.id || 1;
      const res = await api.triggerCanary(tokenId);
      setResult(res);
      onIncidentTriggered();
    } catch (err) {
      console.error(err);
    } finally {
      setInspecting(false);
    }
  };

  useEffect(() => {
    fetchTokens();
  }, []);

  const handleCopy = (id: number, text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const handleInspect = async (cmdToRun?: string) => {
    const cmd = cmdToRun !== undefined ? cmdToRun : commandInput;
    if (!cmd.trim()) return;

    setInspecting(true);
    setResult(null);
    try {
      const res = await api.inspectCommand(cmd);
      setResult(res);
      if (res.blocked) {
        onIncidentTriggered();
      }
    } catch (err: any) {
      console.error(err);
    } finally {
      setInspecting(false);
    }
  };

  const attackPresets = [
    {
      label: 'Agent .env Scavenge',
      cmd: 'cat .env.production',
      desc: 'Simulates agent directly reading production secrets file',
    },
    {
      label: 'PocketOS DB Wipe',
      cmd: 'psql -U admin -c "DROP DATABASE production_cluster;"',
      desc: 'Simulates rogue agent dropping live production database',
    },
    {
      label: 'Railway Token Abuse',
      cmd: tokens.find((t) => t.token_type === 'RAILWAY_PROD_TOKEN')
        ? `railway service delete --token ${
            tokens.find((t) => t.token_type === 'RAILWAY_PROD_TOKEN')?.decoy_value
          }`
        : 'railway delete --token rwy_trap_9901f417b189c4d2',
      desc: 'Simulates exfiltrated railway deployment token execution',
    },
    {
      label: 'AWS Credential Hunt',
      cmd: 'cat ~/.aws/credentials | grep -i secret',
      desc: 'Simulates automated discovery of AWS credentials',
    },
    {
      label: 'Destructive Wipe',
      cmd: 'rm -rf / --no-preserve-root',
      desc: 'Simulates catastrophic root filesystem wipe',
    },
    {
      label: 'Safe Command (Control)',
      cmd: 'pytest backend/tests && git status',
      desc: 'Simulates standard legitimate development commands',
    },
  ];

  return (
    <div className="space-y-6">
      {/* Header Info Banner */}
      <div className="bg-slate-900/90 rounded-2xl p-6 border border-slate-800 shadow-xl backdrop-blur-sm">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2">
              <span className="px-2 py-0.5 text-xs font-mono font-semibold rounded bg-rose-500/10 text-rose-400 border border-rose-500/30">
                MODULE B
              </span>
              <h3 className="text-lg font-bold text-white tracking-tight">
                Anti-Scavenging Honey-Token Trap & Live Canary Tripwire
              </h3>
            </div>
            <p className="text-sm text-slate-400 mt-1 max-w-3xl">
              Deploys tripwire decoy credentials and plants real canary files on disk.
              If an autonomous agent accesses these decoys or attempts destructive shell actions,
              the circuit breaker engages instantly to terminate the agent session.
            </p>
          </div>

          <div className="flex items-center flex-wrap gap-2.5">
            <button
              onClick={handlePlantFile}
              disabled={planting}
              className="px-3.5 py-2 rounded-xl bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white font-medium text-xs flex items-center space-x-1.5 shadow-lg shadow-cyan-500/20 transition-all disabled:opacity-50 active:scale-95"
            >
              <FileCode2 className="h-3.5 w-3.5" />
              <span>{planting ? 'Writing file...' : 'Plant Decoy File on Disk'}</span>
            </button>

            <button
              onClick={handleDeployTokens}
              disabled={loadingTokens}
              className="px-3.5 py-2 rounded-xl bg-gradient-to-r from-rose-600 to-amber-600 hover:from-rose-500 hover:to-amber-500 text-white font-medium text-xs flex items-center space-x-1.5 shadow-lg shadow-rose-500/20 transition-all disabled:opacity-50 active:scale-95"
            >
              <Key className="h-3.5 w-3.5" />
              <span>{loadingTokens ? 'Deploying...' : 'Deploy Decoy Tokens'}</span>
            </button>

            <button
              onClick={handleTestCanary}
              disabled={inspecting}
              className="px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-amber-400 font-mono font-medium text-xs flex items-center space-x-1.5 border border-amber-500/30 transition-all active:scale-95"
            >
              <Radio className="h-3.5 w-3.5 animate-pulse" />
              <span>Test Canary Tripwire</span>
            </button>
          </div>
        </div>

        {/* Planted Decoy Alert */}
        {plantedDecoy && (
          <div className="mt-4 p-3.5 rounded-xl bg-cyan-950/40 border border-cyan-500/30 font-mono text-xs text-cyan-200 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <div>
              <span className="font-bold text-white">DECOY FILE ACTIVE: </span>
              <span className="text-cyan-300">{plantedDecoy.file_path}</span>
            </div>
            <div className="text-[11px] text-slate-400">
              Canary: <span className="text-amber-400 font-semibold">{plantedDecoy.canary_url}</span>
            </div>
          </div>
        )}
      </div>

      {/* Circuit Breaker Alert Banner */}
      {result && result.blocked && (
        <div className="rounded-2xl bg-gradient-to-r from-rose-950/90 via-red-900/70 to-slate-950 p-6 border-2 border-rose-500 shadow-2xl animate-pulse-fast">
          <div className="flex items-start space-x-4">
            <div className="p-3 bg-rose-600 rounded-xl text-white shadow-lg shadow-rose-600/50">
              <AlertOctagon className="h-8 w-8 animate-bounce" />
            </div>
            <div className="flex-1">
              <div className="flex items-center space-x-3">
                <h4 className="text-lg font-black font-mono tracking-wider text-white uppercase">
                  CIRCUIT BREAKER ENGAGED: AGENT TERMINATED
                </h4>
                <span className="px-2.5 py-0.5 rounded text-xs font-mono font-bold bg-rose-500 text-white">
                  {result.severity} VIOLATION
                </span>
              </div>
              <p className="text-rose-200 text-sm mt-1 font-mono">
                {result.explanation}
              </p>

              {/* Matched Details */}
              <div className="mt-4 flex flex-wrap gap-2 text-xs font-mono">
                {result.matched_tokens.map((tok, i) => (
                  <span
                    key={i}
                    className="px-2.5 py-1 rounded bg-rose-900/80 text-rose-200 border border-rose-700 flex items-center space-x-1"
                  >
                    <Flame className="h-3 w-3 text-amber-400" />
                    <span>Honey-Token Tripped: {tok}</span>
                  </span>
                ))}
                {result.matched_patterns.map((pat, i) => (
                  <span
                    key={i}
                    className="px-2.5 py-1 rounded bg-rose-900/80 text-rose-200 border border-rose-700 flex items-center space-x-1"
                  >
                    <ShieldAlert className="h-3 w-3 text-rose-400" />
                    <span>Rule Violation: {pat}</span>
                  </span>
                ))}
                {result.incident_id && (
                  <span className="px-2.5 py-1 rounded bg-slate-900 text-slate-300 border border-slate-700">
                    Incident ID: #{result.incident_id} (Recorded in SQLite)
                  </span>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {result && !result.blocked && (
        <div className="rounded-2xl bg-slate-900/90 p-5 border border-emerald-500/50 shadow-lg flex items-center space-x-4">
          <div className="p-2.5 bg-emerald-500/10 rounded-xl text-emerald-400 border border-emerald-500/30">
            <CheckCircle className="h-6 w-6" />
          </div>
          <div>
            <h4 className="text-sm font-bold font-mono text-emerald-400">
              COMMAND INSPECTION PASSED (ALLOW)
            </h4>
            <p className="text-xs text-slate-300 mt-0.5 font-mono">
              {result.explanation} No tripwire tokens or destructive patterns detected.
            </p>
          </div>
        </div>
      )}

      {/* Interactive Command Simulator */}
      <div className="bg-slate-900/90 rounded-2xl p-6 border border-slate-800 shadow-xl">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center space-x-2">
            <Terminal className="h-4 w-4 text-cyan-400" />
            <span className="text-xs font-mono font-bold uppercase text-slate-300 tracking-wider">
              Agent Command & Tool-Call Inspector
            </span>
          </div>
          <span className="text-xs text-slate-400 font-mono">
            Simulate AI Agent Terminal Invocation
          </span>
        </div>

        {/* Preset Buttons (Shown in Sandbox Mode or as collapsed) */}
        {!isProductionMode && (
          <div className="flex flex-wrap gap-2 mb-4">
            {attackPresets.map((preset, idx) => (
              <button
                key={idx}
                onClick={() => {
                  setCommandInput(preset.cmd);
                  handleInspect(preset.cmd);
                }}
                className="px-3 py-1.5 rounded-lg text-xs font-mono font-medium bg-slate-800/80 hover:bg-slate-700 text-slate-300 hover:text-white border border-slate-700 transition-all flex items-center space-x-1.5 active:scale-95"
              >
                <Zap className="h-3 w-3 text-amber-400" />
                <span>{preset.label}</span>
              </button>
            ))}
          </div>
        )}

        {/* Input Bar */}
        <div className="flex flex-col sm:flex-row gap-3">
          <div className="relative flex-1">
            <span className="absolute left-3.5 top-3 text-cyan-400 font-mono text-sm select-none">
              $&gt;
            </span>
            <input
              type="text"
              value={commandInput}
              onChange={(e) => setCommandInput(e.target.value)}
              placeholder="e.g. cat .env.production or rm -rf /"
              className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-9 pr-4 py-2.5 text-sm font-mono text-slate-200 placeholder-slate-600 focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500"
              onKeyDown={(e) => {
                if (e.key === 'Enter') handleInspect();
              }}
            />
          </div>

          <button
            onClick={() => handleInspect()}
            disabled={inspecting}
            className="px-5 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-cyan-400 font-mono font-semibold text-xs uppercase tracking-wider border border-slate-700 hover:border-cyan-500/50 flex items-center justify-center space-x-2 transition-all disabled:opacity-50"
          >
            <ShieldAlert className="h-4 w-4" />
            <span>{inspecting ? 'Analyzing...' : 'Inspect Command'}</span>
          </button>
        </div>
      </div>

      {/* Active Honey-Tokens Table */}
      <div className="bg-slate-900/90 rounded-2xl p-6 border border-slate-800 shadow-xl">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-2">
            <Key className="h-4 w-4 text-amber-400" />
            <h4 className="text-sm font-bold font-mono text-white uppercase tracking-wider">
              Active Deployed Decoy Honey-Tokens
            </h4>
          </div>
          <button
            onClick={fetchTokens}
            className="text-xs text-slate-400 hover:text-white flex items-center space-x-1"
          >
            <RefreshCw className="h-3 w-3" />
            <span>Refresh Table</span>
          </button>
        </div>

        <div className="overflow-x-auto rounded-xl border border-slate-800">
          <table className="w-full text-left text-xs font-mono text-slate-300">
            <thead className="bg-slate-950 text-slate-400 uppercase text-[10px] tracking-wider border-b border-slate-800">
              <tr>
                <th className="py-2.5 px-4">Token Type</th>
                <th className="py-2.5 px-4">Environment Key</th>
                <th className="py-2.5 px-4">Decoy Value (Tripwire)</th>
                <th className="py-2.5 px-4">Filepath Hint</th>
                <th className="py-2.5 px-4">Trap Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 bg-slate-900/50">
              {tokens.length > 0 ? (
                tokens.map((token) => (
                  <tr key={token.id} className="hover:bg-slate-800/40">
                    <td className="py-2.5 px-4 font-bold text-amber-300">
                      {token.token_type}
                    </td>
                    <td className="py-2.5 px-4 text-slate-300">{token.decoy_key}</td>
                    <td className="py-2.5 px-4">
                      <div className="flex items-center space-x-2">
                        <span className="font-mono text-rose-300 bg-rose-500/10 px-2 py-0.5 rounded border border-rose-500/20">
                          {token.decoy_value.slice(0, 16)}...
                        </span>
                        <button
                          onClick={() => handleCopy(token.id, token.decoy_value)}
                          className="p-1 rounded hover:bg-slate-800 text-slate-400 hover:text-slate-200 transition-colors"
                          title="Copy Full Decoy Token"
                        >
                          {copiedId === token.id ? (
                            <Check className="h-3.5 w-3.5 text-emerald-400" />
                          ) : (
                            <Copy className="h-3.5 w-3.5" />
                          )}
                        </button>
                      </div>
                    </td>
                    <td className="py-2.5 px-4 text-slate-400">{token.filepath_hint}</td>
                    <td className="py-2.5 px-4">
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 flex items-center space-x-1 w-fit">
                        <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
                        <span>{token.status}</span>
                      </span>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={5} className="py-8 text-center text-slate-500">
                    No active honey tokens found. Click &ldquo;Deploy Decoy Tokens&rdquo; to seed the database.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
