import React, { useState, useEffect } from 'react';
import { Activity, Zap, DollarSign, Clock, ShieldAlert, FileText, CheckCircle2 } from 'lucide-react';
import { api } from '../services/api';

export default function AnalyticsView() {
  const [summary, setSummary] = useState(null);
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchAnalytics = async () => {
    try {
      setLoading(true);
      const [sumData, logData] = await Promise.all([
        api.getAnalyticsSummary(),
        api.getTelemetryLogs(40)
      ]);
      setSummary(sumData);
      setLogs(logData);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalytics();
  }, []);

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-xl font-bold text-white tracking-tight">Observability, Cost & Telemetry</h2>
        <p className="text-sm text-slate-400">
          Live monitoring of token consumption, USD compute costs, latency percentiles, and multi-model fallback activations.
        </p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-slate-900/70 border border-slate-800 p-5 rounded-2xl shadow-lg">
          <div className="flex items-center justify-between text-slate-400 text-xs font-mono mb-2">
            <span>TOTAL QUERIES</span>
            <Activity className="w-4 h-4 text-sky-400" />
          </div>
          <p className="text-2xl font-bold text-white font-mono">{summary?.total_queries || 0}</p>
          <span className="text-xs text-slate-500 mt-1 block">RAG + Autonomous Agent calls</span>
        </div>

        <div className="bg-slate-900/70 border border-slate-800 p-5 rounded-2xl shadow-lg">
          <div className="flex items-center justify-between text-slate-400 text-xs font-mono mb-2">
            <span>TOTAL TOKENS</span>
            <Zap className="w-4 h-4 text-amber-400" />
          </div>
          <p className="text-2xl font-bold text-white font-mono">{summary?.total_tokens?.toLocaleString() || 0}</p>
          <span className="text-xs text-slate-500 mt-1 block">Prompt + Completion Tokens</span>
        </div>

        <div className="bg-slate-900/70 border border-slate-800 p-5 rounded-2xl shadow-lg">
          <div className="flex items-center justify-between text-slate-400 text-xs font-mono mb-2">
            <span>ESTIMATED COST</span>
            <DollarSign className="w-4 h-4 text-emerald-400" />
          </div>
          <p className="text-2xl font-bold text-emerald-400 font-mono">${summary?.total_cost_usd?.toFixed(4) || '0.0000'}</p>
          <span className="text-xs text-slate-500 mt-1 block">Tracked per-invocation compute</span>
        </div>

        <div className="bg-slate-900/70 border border-slate-800 p-5 rounded-2xl shadow-lg">
          <div className="flex items-center justify-between text-slate-400 text-xs font-mono mb-2">
            <span>AVG LATENCY</span>
            <Clock className="w-4 h-4 text-purple-400" />
          </div>
          <p className="text-2xl font-bold text-white font-mono">{summary?.avg_latency_ms || 0} ms</p>
          <span className="text-xs text-slate-500 mt-1 block">End-to-end response time</span>
        </div>
      </div>

      {/* Secondary Status Row */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-slate-900/50 border border-slate-800 p-4 rounded-xl flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="p-2 rounded-lg bg-sky-500/10 text-sky-400">
              <FileText className="w-5 h-5" />
            </div>
            <div>
              <p className="text-sm font-medium text-white">Active Indexed Documents</p>
              <p className="text-xs text-slate-500">Live in ChromaDB & BM25 sparse index</p>
            </div>
          </div>
          <span className="text-lg font-bold text-white font-mono">{summary?.active_documents || 0}</span>
        </div>

        <div className="bg-slate-900/50 border border-slate-800 p-4 rounded-xl flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="p-2 rounded-lg bg-amber-500/10 text-amber-400">
              <ShieldAlert className="w-5 h-5" />
            </div>
            <div>
              <p className="text-sm font-medium text-white">Fallback Circuit Triggers</p>
              <p className="text-xs text-slate-500">Automatic secondary model reroutes</p>
            </div>
          </div>
          <span className="text-lg font-bold text-amber-400 font-mono">{summary?.fallback_count || 0}</span>
        </div>
      </div>

      {/* Query Telemetry Logs Table */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
        <div className="px-6 py-4 border-b border-slate-800">
          <span className="font-semibold text-slate-200 text-sm">Real-Time Invocation Audit Trail</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead className="bg-slate-950/80 text-slate-400 border-b border-slate-800">
              <tr>
                <th className="py-3 px-4">Endpoint</th>
                <th className="py-3 px-4">Model & Provider</th>
                <th className="py-3 px-4">Query Excerpt</th>
                <th className="py-3 px-4">Tokens</th>
                <th className="py-3 px-4">Latency</th>
                <th className="py-3 px-4">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-slate-300">
              {logs.length === 0 ? (
                <tr>
                  <td colSpan="6" className="py-8 text-center text-slate-500 font-sans">
                    No query invocations recorded yet.
                  </td>
                </tr>
              ) : (
                logs.map((log) => (
                  <tr key={log.id} className="hover:bg-slate-800/30 transition-colors">
                    <td className="py-3 px-4 text-sky-400 font-semibold">{log.endpoint}</td>
                    <td className="py-3 px-4">
                      <span>{log.model}</span>
                      {log.fallback_triggered && (
                        <span className="ml-1 text-[10px] text-amber-400 bg-amber-500/10 px-1 py-0.5 rounded border border-amber-500/30">
                          Fallback
                        </span>
                      )}
                    </td>
                    <td className="py-3 px-4 truncate max-w-xs text-slate-400">
                      {log.query || 'N/A'}
                    </td>
                    <td className="py-3 px-4">{log.total_tokens}</td>
                    <td className="py-3 px-4">{log.latency_ms}ms</td>
                    <td className="py-3 px-4">
                      {log.status_code === 200 ? (
                        <span className="text-emerald-400 flex items-center space-x-1">
                          <CheckCircle2 className="w-3.5 h-3.5" />
                          <span>200 OK</span>
                        </span>
                      ) : (
                        <span className="text-rose-400 font-semibold">{log.status_code}</span>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
