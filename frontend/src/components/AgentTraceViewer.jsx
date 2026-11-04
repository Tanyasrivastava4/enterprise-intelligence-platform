import React, { useState } from 'react';
import { ChevronDown, ChevronRight, Wrench, CheckCircle, Clock, AlertTriangle, FileCode } from 'lucide-react';

export default function AgentTraceViewer({ steps, toolsUsed, totalLatency, totalTokens }) {
  const [isOpen, setIsOpen] = useState(false);
  const [expandedStep, setExpandedStep] = useState(null);

  if (!steps || steps.length === 0) return null;

  return (
    <div className="mt-3 border border-slate-700/80 bg-slate-950/70 rounded-xl overflow-hidden shadow-inner text-xs">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full px-4 py-2.5 flex items-center justify-between text-slate-300 hover:text-white hover:bg-slate-900/60 transition-colors"
      >
        <div className="flex items-center space-x-2">
          <Wrench className="w-4 h-4 text-amber-400" />
          <span className="font-semibold text-slate-200">
            Agent Execution Chain ({steps.length} Tool Steps)
          </span>
          <span className="text-[11px] text-slate-400 font-mono">
            [{toolsUsed?.join(' → ')}]
          </span>
        </div>
        <div className="flex items-center space-x-3 text-slate-400">
          <span className="flex items-center space-x-1">
            <Clock className="w-3.5 h-3.5 text-slate-500" />
            <span>{totalLatency}ms</span>
          </span>
          {isOpen ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
        </div>
      </button>

      {isOpen && (
        <div className="p-4 pt-1 space-y-3 border-t border-slate-800/80 bg-slate-950">
          {steps.map((step, idx) => {
            const isStepOpen = expandedStep === idx;
            const isSuccess = step.status === 'success';

            return (
              <div
                key={idx}
                className="border border-slate-800 rounded-lg bg-slate-900/60 overflow-hidden"
              >
                <div
                  onClick={() => setExpandedStep(isStepOpen ? null : idx)}
                  className="px-3 py-2 flex items-center justify-between cursor-pointer hover:bg-slate-800/50"
                >
                  <div className="flex items-center space-x-2">
                    <span className="w-5 h-5 rounded-full bg-slate-800 flex items-center justify-center font-mono text-[10px] text-slate-300">
                      {step.step_number || idx + 1}
                    </span>
                    <span className="font-mono font-medium text-sky-400">{step.tool_name}</span>
                    {isSuccess ? (
                      <CheckCircle className="w-3.5 h-3.5 text-emerald-400" />
                    ) : (
                      <AlertTriangle className="w-3.5 h-3.5 text-rose-400" />
                    )}
                  </div>
                  <div className="flex items-center space-x-2 text-slate-400 font-mono text-[11px]">
                    <span>{step.latency_ms}ms</span>
                    {isStepOpen ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronRight className="w-3.5 h-3.5" />}
                  </div>
                </div>

                {isStepOpen && (
                  <div className="p-3 border-t border-slate-800 space-y-2 bg-slate-950/80">
                    <div>
                      <span className="text-[10px] font-mono text-slate-500 uppercase">Input Parameters:</span>
                      <pre className="mt-1 p-2 bg-slate-900 rounded font-mono text-[11px] text-slate-300 overflow-x-auto border border-slate-800/60">
                        {JSON.stringify(step.tool_input, null, 2)}
                      </pre>
                    </div>
                    <div>
                      <span className="text-[10px] font-mono text-slate-500 uppercase">Output Result:</span>
                      <pre className="mt-1 p-2 bg-slate-900 rounded font-mono text-[11px] text-slate-300 overflow-x-auto border border-slate-800/60 max-h-48">
                        {typeof step.tool_output === 'string'
                          ? step.tool_output
                          : JSON.stringify(step.tool_output, null, 2)}
                      </pre>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
