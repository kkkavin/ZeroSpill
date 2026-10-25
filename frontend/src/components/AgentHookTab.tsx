import React, { useState, useEffect } from 'react';
import {
  GitBranch,
  ShieldCheck,
  CheckCircle2,
  XCircle,
  Copy,
  Check,
  Terminal,
  Cpu,
  Layers,
  ArrowRight,
  RefreshCw,
} from 'lucide-react';
import { api, AgentHookStatusResponse } from '../services/api';

export const AgentHookTab: React.FC = () => {
  const [status, setStatus] = useState<AgentHookStatusResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [installing, setInstalling] = useState<boolean>(false);
  const [copiedCmd, setCopiedCmd] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const fetchStatus = async () => {
    setLoading(true);
    try {
      const data = await api.getAgentHookStatus();
      setStatus(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleInstall = async () => {
    setInstalling(true);
    setMessage(null);
    try {
      const res = await api.installAgentHook();
      setMessage(res.message);
      await fetchStatus();
    } catch (err: any) {
      setMessage(err?.message || 'Failed to install git hook.');
    } finally {
      setInstalling(false);
    }
  };

  useEffect(() => {
    fetchStatus();
  }, []);

  const handleCopy = (cmd: string) => {
    navigator.clipboard.writeText(cmd);
    setCopiedCmd(cmd);
    setTimeout(() => setCopiedCmd(null), 2000);
  };

  const cliCommands = [
    {
      label: 'Scan All Staged Files (Pre-Commit Gate)',
      cmd: 'python zerospill_cli.py scan-staged',
      desc: 'Audits all git staged images via RapidOCR and text traces through Airlock. Exits 1 if leaks found.',
    },
    {
      label: '1-Click Install Git Pre-Commit Hook',
      cmd: 'python zerospill_cli.py install-hook',
      desc: 'Writes .git/hooks/pre-commit and .agents/rules/zerospill-guard.md into local repository.',
    },
    {
      label: 'Check Hook & Guard Status',
      cmd: 'python zerospill_cli.py status',
      desc: 'Verifies active defense guardrails on the local agent filesystem.',
    },
  ];

  return (
    <div className="space-y-6">
      {/* Header Info Banner */}
      <div className="bg-slate-900/90 rounded-2xl p-6 border border-slate-800 shadow-xl backdrop-blur-sm">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2">
              <span className="px-2 py-0.5 text-xs font-mono font-semibold rounded bg-purple-500/10 text-purple-400 border border-purple-500/30">
                MODULE D &bull; AGENT INTERCEPTOR
              </span>
              <h3 className="text-lg font-bold text-white tracking-tight">
                Git Pre-Commit Hook & Autonomous Agent Airlock
              </h3>
            </div>
            <p className="text-sm text-slate-400 mt-1 max-w-3xl">
              Connects ZeroSpill directly into local AI coding agent workflows (Devin, Cline, SWE-agent, OpenHands).
              Screenshots and staged commits are autonomously intercepted at the Git level, aborting commits before secrets reach GitHub.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={handleInstall}
              disabled={installing}
              className="px-4 py-2.5 rounded-xl bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white font-medium text-sm flex items-center space-x-2 shadow-lg shadow-purple-500/20 transition-all disabled:opacity-50 active:scale-95"
            >
              <GitBranch className="h-4 w-4" />
              <span>{installing ? 'Installing Hook...' : '1-Click Install Git Hook'}</span>
            </button>
          </div>
        </div>

        {message && (
          <div className="mt-4 p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs flex items-center space-x-2 font-mono">
            <CheckCircle2 className="h-4 w-4 shrink-0" />
            <span>{message}</span>
          </div>
        )}
      </div>

      {/* Live Guardrail Status Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Hook Status */}
        <div className="bg-slate-900/90 rounded-2xl p-5 border border-slate-800 shadow-lg">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2.5">
              <div className="p-2.5 rounded-xl bg-purple-500/10 text-purple-400 border border-purple-500/30">
                <GitBranch className="h-5 w-5" />
              </div>
              <div>
                <h4 className="text-sm font-bold text-white">Git Pre-Commit Hook</h4>
                <p className="text-xs text-slate-400 font-mono mt-0.5">.git/hooks/pre-commit</p>
              </div>
            </div>
            {status?.hook_installed ? (
              <span className="flex items-center space-x-1 px-2.5 py-1 rounded-full text-xs font-mono font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                <CheckCircle2 className="h-3.5 w-3.5" />
                <span>ARMED & ACTIVE</span>
              </span>
            ) : (
              <span className="flex items-center space-x-1 px-2.5 py-1 rounded-full text-xs font-mono font-bold bg-rose-500/10 text-rose-400 border border-rose-500/30">
                <XCircle className="h-3.5 w-3.5" />
                <span>NOT INSTALLED</span>
              </span>
            )}
          </div>
          <p className="text-xs text-slate-400 mt-3 font-mono">
            Intercepts every local <code className="text-purple-300">git commit</code> executed by human or autonomous agents.
          </p>
        </div>

        {/* Rule Status */}
        <div className="bg-slate-900/90 rounded-2xl p-5 border border-slate-800 shadow-lg">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2.5">
              <div className="p-2.5 rounded-xl bg-cyan-500/10 text-cyan-400 border border-cyan-500/30">
                <ShieldCheck className="h-5 w-5" />
              </div>
              <div>
                <h4 className="text-sm font-bold text-white">Agent Guardrail Protocol</h4>
                <p className="text-xs text-slate-400 font-mono mt-0.5">.agents/rules/zerospill-guard.md</p>
              </div>
            </div>
            {status?.rule_installed ? (
              <span className="flex items-center space-x-1 px-2.5 py-1 rounded-full text-xs font-mono font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                <CheckCircle2 className="h-3.5 w-3.5" />
                <span>ENFORCED</span>
              </span>
            ) : (
              <span className="flex items-center space-x-1 px-2.5 py-1 rounded-full text-xs font-mono font-bold bg-rose-500/10 text-rose-400 border border-rose-500/30">
                <XCircle className="h-3.5 w-3.5" />
                <span>MISSING</span>
              </span>
            )}
          </div>
          <p className="text-xs text-slate-400 mt-3 font-mono">
            Mandates all autonomous coding agents to sanitize screenshots and respect honey-tokens.
          </p>
        </div>
      </div>

      {/* CLI Command Quick-Access */}
      <div className="bg-slate-900/90 rounded-2xl p-6 border border-slate-800 shadow-xl">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-2">
            <Terminal className="h-4 w-4 text-cyan-400" />
            <h4 className="text-sm font-bold font-mono text-white uppercase tracking-wider">
              ZeroSpill CLI Commands (`zerospill_cli.py`)
            </h4>
          </div>
          <button
            onClick={fetchStatus}
            className="text-xs text-slate-400 hover:text-white flex items-center space-x-1"
          >
            <RefreshCw className={`h-3 w-3 ${loading ? 'animate-spin' : ''}`} />
            <span>Refresh Status</span>
          </button>
        </div>

        <div className="space-y-3">
          {cliCommands.map((item, idx) => (
            <div
              key={idx}
              className="p-4 rounded-xl bg-slate-950/70 border border-slate-800/80 flex flex-col sm:flex-row sm:items-center justify-between gap-3 hover:border-slate-700 transition-colors"
            >
              <div>
                <p className="text-xs font-bold text-slate-200">{item.label}</p>
                <code className="text-xs font-mono text-cyan-300 mt-1 block select-all">
                  {item.cmd}
                </code>
                <p className="text-[11px] text-slate-400 mt-1">{item.desc}</p>
              </div>

              <button
                onClick={() => handleCopy(item.cmd)}
                className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-mono flex items-center space-x-1.5 shrink-0 self-start sm:self-center transition-colors"
              >
                {copiedCmd === item.cmd ? (
                  <>
                    <Check className="h-3.5 w-3.5 text-emerald-400" />
                    <span>Copied!</span>
                  </>
                ) : (
                  <>
                    <Copy className="h-3.5 w-3.5" />
                    <span>Copy Command</span>
                  </>
                )}
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* Architecture Flow Explanation */}
      <div className="bg-slate-900/60 rounded-2xl p-6 border border-slate-800">
        <h4 className="text-xs font-mono font-bold uppercase text-slate-400 tracking-wider mb-4 flex items-center space-x-2">
          <Layers className="h-4 w-4 text-purple-400" />
          <span>How ZeroSpill Guards Autonomous Coding Agents</span>
        </h4>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs font-mono">
          <div className="p-3.5 rounded-xl bg-slate-950/50 border border-slate-800 space-y-1.5">
            <div className="flex items-center space-x-1.5 text-cyan-400 font-bold">
              <span>1. Screenshot Ingestion</span>
              <ArrowRight className="h-3 w-3" />
            </div>
            <p className="text-slate-400">
              Agent captures desktop or browser view. ZeroSpill RapidOCR detects API keys, URIs, or PII and applies Gaussian blur before saving.
            </p>
          </div>

          <div className="p-3.5 rounded-xl bg-slate-950/50 border border-slate-800 space-y-1.5">
            <div className="flex items-center space-x-1.5 text-amber-400 font-bold">
              <span>2. Tool & Command Execution</span>
              <ArrowRight className="h-3 w-3" />
            </div>
            <p className="text-slate-400">
              Agent runs bash tool calls. If decoy credentials or destructive scripts are triggered, the circuit-breaker terminates the agent session.
            </p>
          </div>

          <div className="p-3.5 rounded-xl bg-slate-950/50 border border-slate-800 space-y-1.5">
            <div className="flex items-center space-x-1.5 text-emerald-400 font-bold">
              <span>3. Git Pre-Commit Gate</span>
            </div>
            <p className="text-slate-400">
              Before code or transcripts reach GitHub, `zerospill_cli.py scan-staged` audits all assets, blocking commits if leaks persist.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
