import React from 'react';
import { X, FileText, CheckCircle2, Bookmark } from 'lucide-react';

export default function CitationDrawer({ citation, onClose }) {
  if (!citation) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-hidden bg-black/60 backdrop-blur-sm flex justify-end animate-fadeIn">
      <div className="w-full max-w-md bg-slate-900 border-l border-slate-800 h-full p-6 flex flex-col shadow-2xl">
        <div className="flex items-center justify-between pb-4 border-b border-slate-800">
          <div className="flex items-center space-x-2 text-sky-400">
            <Bookmark className="w-5 h-5" />
            <h3 className="font-semibold text-white text-base">Verified Source Citation</h3>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="mt-6 space-y-4 flex-1 overflow-y-auto">
          <div className="bg-slate-950/60 p-4 rounded-xl border border-slate-800/80">
            <div className="flex items-center space-x-2 text-xs font-mono text-slate-400 mb-1">
              <FileText className="w-4 h-4 text-sky-400" />
              <span>SOURCE DOCUMENT</span>
            </div>
            <p className="text-white font-medium text-sm break-all">{citation.document_name}</p>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="bg-slate-950/60 p-3 rounded-xl border border-slate-800/80">
              <span className="text-xs font-mono text-slate-400">LOCATION</span>
              <p className="text-sm font-semibold text-white mt-0.5">Page / Row {citation.page_or_row}</p>
            </div>
            <div className="bg-slate-950/60 p-3 rounded-xl border border-slate-800/80">
              <span className="text-xs font-mono text-slate-400">SIMILARITY SCORE</span>
              <p className="text-sm font-semibold text-emerald-400 mt-0.5">
                {(citation.similarity_score * 100).toFixed(1)}% match
              </p>
            </div>
          </div>

          <div className="bg-slate-950/60 p-4 rounded-xl border border-slate-800/80">
            <div className="flex items-center justify-between text-xs font-mono text-slate-400 mb-2">
              <span>VERBATIM CHUNK EVIDENCE</span>
              <span className="text-emerald-400 flex items-center space-x-1">
                <CheckCircle2 className="w-3.5 h-3.5" />
                <span>Grounded</span>
              </span>
            </div>
            <div className="p-3 bg-slate-900 rounded-lg text-xs font-mono text-slate-300 leading-relaxed border border-slate-800/50 max-h-64 overflow-y-auto whitespace-pre-wrap">
              {citation.excerpt}
            </div>
          </div>

          <div className="text-[11px] text-slate-500 font-mono">
            Chunk ID: <span className="text-slate-400">{citation.chunk_id}</span>
          </div>
        </div>

        <div className="pt-4 border-t border-slate-800">
          <button
            onClick={onClose}
            className="w-full py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-sm font-medium rounded-lg transition-colors"
          >
            Close Inspector
          </button>
        </div>
      </div>
    </div>
  );
}
