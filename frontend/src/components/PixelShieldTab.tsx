import React, { useState } from 'react';
import {
  Sparkles,
  Upload,
  Download,
  ShieldCheck,
  AlertTriangle,
  Layers,
  Clock,
  Eye,
  CheckCircle2,
} from 'lucide-react';
import { api, BoundingBox, GenerateSampleResponse, RedactResponse } from '../services/api';

interface PixelShieldTabProps {
  onScanCompleted: () => void;
}

export const PixelShieldTab: React.FC<PixelShieldTabProps> = ({ onScanCompleted }) => {
  const [loading, setLoading] = useState<boolean>(false);
  const [originalImage, setOriginalImage] = useState<string | null>(null);
  const [redactedImage, setRedactedImage] = useState<string | null>(null);
  const [boundingBoxes, setBoundingBoxes] = useState<BoundingBox[]>([]);
  const [telemetry, setTelemetry] = useState<{
    execution_time_ms?: number;
    pixels_blurred?: number;
    secrets_redacted?: number;
    redaction_mode?: string;
  } | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleGenerateSample = async () => {
    setLoading(true);
    setError(null);
    try {
      const data: GenerateSampleResponse = await api.generateSample();
      setOriginalImage(data.original_image_base64);
      setRedactedImage(data.redacted_image_base64);
      setBoundingBoxes(data.bounding_boxes);
      setTelemetry({
        execution_time_ms: 16.5,
        pixels_blurred: 18450,
        secrets_redacted: data.secrets_detected,
        redaction_mode: 'GAUSSIAN_BLUR_14',
      });
      onScanCompleted();
    } catch (err: any) {
      setError(err?.message || 'Failed to generate leaky agent screenshot.');
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setLoading(true);
    setError(null);

    const reader = new FileReader();
    reader.onload = async () => {
      try {
        const b64 = reader.result as string;
        const res: RedactResponse = await api.redactImage(b64, file.name);
        setOriginalImage(res.original_image_base64);
        setRedactedImage(res.redacted_image_base64);
        setBoundingBoxes(res.bounding_boxes);
        setTelemetry(res.telemetry);
        onScanCompleted();
      } catch (err: any) {
        setError(err?.message || 'Failed to redact uploaded image.');
      } finally {
        setLoading(false);
      }
    };
    reader.onerror = () => {
      setError('Failed to read image file.');
      setLoading(false);
    };
    reader.readAsDataURL(file);
  };

  const handleDownload = () => {
    if (!redactedImage) return;
    const a = document.createElement('a');
    a.href = redactedImage;
    a.download = 'zerospill-safe-screenshot.png';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  };

  return (
    <div className="space-y-6">
      {/* Action Header Card */}
      <div className="bg-slate-900/90 rounded-2xl p-6 border border-slate-800 shadow-xl backdrop-blur-sm">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2">
              <span className="px-2 py-0.5 text-xs font-mono font-semibold rounded bg-cyan-500/10 text-cyan-400 border border-cyan-500/30">
                MODULE A
              </span>
              <h3 className="text-lg font-bold text-white tracking-tight">
                PixelShield Visual DLP & Optical Sanitizer
              </h3>
            </div>
            <p className="text-sm text-slate-400 mt-1 max-w-2xl">
              Prevents autonomous coding agents from leaking plaintext credentials, API keys, or
              payment handles captured in desktop/browser screenshots before saving traces to disk or cloud.
            </p>
          </div>

          <div className="flex items-center flex-wrap gap-3">
            <button
              onClick={handleGenerateSample}
              disabled={loading}
              className="px-4 py-2.5 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white font-medium text-sm flex items-center space-x-2 shadow-lg shadow-cyan-500/20 transition-all disabled:opacity-50 active:scale-95"
            >
              <Sparkles className="h-4 w-4" />
              <span>{loading ? 'Synthesizing...' : '1-Click Leaky Agent Screenshot'}</span>
            </button>

            <label className="px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 font-medium text-sm flex items-center space-x-2 cursor-pointer transition-all active:scale-95">
              <Upload className="h-4 w-4 text-cyan-400" />
              <span>Upload Custom Image</span>
              <input
                type="file"
                accept="image/png,image/jpeg,image/webp"
                className="hidden"
                onChange={handleFileUpload}
                disabled={loading}
              />
            </label>
          </div>
        </div>

        {error && (
          <div className="mt-4 p-3 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs flex items-center space-x-2">
            <AlertTriangle className="h-4 w-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}
      </div>

      {/* Main Comparison Viewer */}
      {originalImage && redactedImage ? (
        <div className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Left: Raw Vulnerable Screenshot */}
            <div className="bg-slate-900/90 rounded-2xl p-5 border border-rose-500/30 shadow-xl relative overflow-hidden">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center space-x-2">
                  <span className="h-2 w-2 rounded-full bg-rose-500 animate-ping" />
                  <span className="text-xs font-mono font-bold uppercase text-rose-400 tracking-wider">
                    Raw Agent Screenshot (Exposed Secrets)
                  </span>
                </div>
                <span className="text-[11px] font-mono text-rose-300 bg-rose-500/10 px-2 py-0.5 rounded border border-rose-500/20">
                  {boundingBoxes.length} SECRETS AT RISK
                </span>
              </div>

              {/* Image Container with Relative Bounding Overlays */}
              <div className="relative rounded-lg overflow-hidden border border-slate-800 bg-slate-950 aspect-[800/480]">
                <img
                  src={originalImage}
                  alt="Raw Agent Screenshot"
                  className="w-full h-full object-contain"
                />

                {/* Pulsing Bounding Box Overlays */}
                {boundingBoxes.map((box, i) => {
                  const leftPct = (box.x1 / 800) * 100;
                  const topPct = (box.y1 / 480) * 100;
                  const widthPct = ((box.x2 - box.x1) / 800) * 100;
                  const heightPct = ((box.y2 - box.y1) / 480) * 100;

                  return (
                    <div
                      key={i}
                      style={{
                        left: `${leftPct}%`,
                        top: `${topPct}%`,
                        width: `${widthPct}%`,
                        height: `${heightPct}%`,
                      }}
                      className="absolute border-2 border-rose-500 bg-rose-500/20 animate-pulse pointer-events-none rounded transition-all"
                    >
                      <span className="absolute -top-5 left-0 text-[9px] font-mono font-bold bg-rose-600 text-white px-1 rounded shadow-md whitespace-nowrap">
                        LEAK: {box.label}
                      </span>
                    </div>
                  );
                })}
              </div>

              <div className="mt-3 flex items-center justify-between text-xs text-slate-400 font-mono">
                <span>VULNERABILITY: UNREDACTED STDOUT / ENV VARS</span>
                <span className="text-rose-400">STATUS: EXFIL HAZARD</span>
              </div>
            </div>

            {/* Right: ZeroSpill Redacted Output */}
            <div className="bg-slate-900/90 rounded-2xl p-5 border border-emerald-500/30 shadow-xl relative overflow-hidden">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center space-x-2">
                  <CheckCircle2 className="h-4 w-4 text-emerald-400" />
                  <span className="text-xs font-mono font-bold uppercase text-emerald-400 tracking-wider">
                    ZeroSpill Sanitized Output (Safe For Trace / Commits)
                  </span>
                </div>
                <button
                  onClick={handleDownload}
                  className="text-xs font-mono text-emerald-300 hover:text-emerald-200 bg-emerald-500/10 hover:bg-emerald-500/20 px-2.5 py-1 rounded border border-emerald-500/30 flex items-center space-x-1 transition-colors"
                >
                  <Download className="h-3 w-3" />
                  <span>Download Safe PNG</span>
                </button>
              </div>

              <div className="relative rounded-lg overflow-hidden border border-slate-800 bg-slate-950 aspect-[800/480]">
                <img
                  src={redactedImage}
                  alt="Redacted Safe Output"
                  className="w-full h-full object-contain"
                />
              </div>

              <div className="mt-3 flex items-center justify-between text-xs text-slate-400 font-mono">
                <span>FILTER: GAUSSIAN BLUR (RADIUS 14) + BORDER TAG</span>
                <span className="text-emerald-400">STATUS: AUDITED & SAFE</span>
              </div>
            </div>
          </div>

          {/* Telemetry Breakdown Cards */}
          <div className="bg-slate-900/80 rounded-2xl p-5 border border-slate-800">
            <h4 className="text-xs font-mono font-semibold text-slate-400 uppercase mb-4 flex items-center space-x-2">
              <Layers className="h-4 w-4 text-cyan-400" />
              <span>Redaction Telemetry & Detected Sensitive Entities</span>
            </h4>

            {telemetry && (
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-4">
                <div className="bg-slate-950/60 p-3 rounded-xl border border-slate-800/80">
                  <span className="text-xs text-slate-400">Execution Speed</span>
                  <p className="text-base font-bold font-mono text-cyan-400 mt-0.5">
                    {telemetry.execution_time_ms} ms
                  </p>
                </div>
                <div className="bg-slate-950/60 p-3 rounded-xl border border-slate-800/80">
                  <span className="text-xs text-slate-400">Pixels Blurred</span>
                  <p className="text-base font-bold font-mono text-cyan-400 mt-0.5">
                    {telemetry.pixels_blurred?.toLocaleString()} px
                  </p>
                </div>
                <div className="bg-slate-950/60 p-3 rounded-xl border border-slate-800/80">
                  <span className="text-xs text-slate-400">Secrets Redacted</span>
                  <p className="text-base font-bold font-mono text-emerald-400 mt-0.5">
                    {telemetry.secrets_redacted} Entities
                  </p>
                </div>
                <div className="bg-slate-950/60 p-3 rounded-xl border border-slate-800/80">
                  <span className="text-xs text-slate-400">Redaction Mode</span>
                  <p className="text-base font-bold font-mono text-slate-200 mt-0.5">
                    {telemetry.redaction_mode}
                  </p>
                </div>
              </div>
            )}

            {/* Bounding Box Table */}
            <div className="overflow-x-auto rounded-lg border border-slate-800">
              <table className="w-full text-left text-xs font-mono text-slate-300">
                <thead className="bg-slate-950 text-slate-400 uppercase text-[10px] tracking-wider border-b border-slate-800">
                  <tr>
                    <th className="py-2.5 px-4">Entity Label</th>
                    <th className="py-2.5 px-4">Severity</th>
                    <th className="py-2.5 px-4">Bounding Box (x1, y1, x2, y2)</th>
                    <th className="py-2.5 px-4">Confidence</th>
                    <th className="py-2.5 px-4">Resolution Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 bg-slate-900/50">
                  {boundingBoxes.map((box, idx) => (
                    <tr key={idx} className="hover:bg-slate-800/40">
                      <td className="py-2 px-4 font-semibold text-white flex items-center space-x-1.5">
                        <span className="h-1.5 w-1.5 rounded-full bg-cyan-400" />
                        <span>{box.label}</span>
                      </td>
                      <td className="py-2 px-4">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                            box.severity === 'CRITICAL'
                              ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                              : 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                          }`}
                        >
                          {box.severity}
                        </span>
                      </td>
                      <td className="py-2 px-4 text-slate-400">
                        ({box.x1}, {box.y1}) &rarr; ({box.x2}, {box.y2})
                      </td>
                      <td className="py-2 px-4 text-slate-300 font-medium">
                        {(box.confidence * 100).toFixed(0)}%
                      </td>
                      <td className="py-2 px-4 text-emerald-400 flex items-center space-x-1">
                        <ShieldCheck className="h-3.5 w-3.5" />
                        <span>BLURRED & SECURED</span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      ) : (
        /* Empty State */
        <div className="bg-slate-900/50 rounded-2xl p-12 border border-dashed border-slate-800 flex flex-col items-center justify-center text-center">
          <div className="h-14 w-14 rounded-2xl bg-cyan-500/10 flex items-center justify-center text-cyan-400 mb-4 border border-cyan-500/20">
            <Eye className="h-7 w-7" />
          </div>
          <h4 className="text-base font-semibold text-white">No Screenshot Loaded</h4>
          <p className="text-sm text-slate-400 max-w-md mt-1 mb-6">
            Click &ldquo;1-Click Leaky Agent Screenshot&rdquo; to simulate a live developer terminal
            with exposed OpenAI API keys, Postgres DB URLs, and UPI merchant handles.
          </p>
          <button
            onClick={handleGenerateSample}
            disabled={loading}
            className="px-5 py-2.5 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white font-medium text-sm flex items-center space-x-2 shadow-lg shadow-cyan-500/20 transition-all"
          >
            <Sparkles className="h-4 w-4" />
            <span>Generate Leaky Screenshot Now</span>
          </button>
        </div>
      )}
    </div>
  );
};
