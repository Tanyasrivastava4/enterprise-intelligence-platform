import React from 'react';
import { Bot, FileText, Layers, Activity, ShieldCheck } from 'lucide-react';

export default function Navbar({ activeTab, setActiveTab, user }) {
  const tabs = [
    { id: 'chat', label: 'AI Intelligence Chat', icon: Bot },
    { id: 'agent', label: 'Autonomous Agent', icon: Layers },
    { id: 'documents', label: 'Document Intelligence', icon: FileText },
    { id: 'analytics', label: 'Observability & Metrics', icon: Activity }
  ];

  return (
    <header className="bg-slate-950 border-b border-slate-800 sticky top-0 z-40">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center space-x-3">
            <div className="h-9 w-9 rounded-lg bg-sky-500/20 border border-sky-500/40 flex items-center justify-center text-sky-400 font-bold">
              AI
            </div>
            <div>
              <span className="font-semibold text-white tracking-wide text-sm sm:text-base">
                Enterprise Intelligence Platform
              </span>
              <span className="hidden sm:inline-block ml-2 px-2 py-0.5 text-xs font-mono rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                v1.0 Ready
              </span>
            </div>
          </div>

          <nav className="flex space-x-1 sm:space-x-2">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center space-x-2 px-3 py-2 rounded-lg text-xs sm:text-sm font-medium transition-colors ${
                    isActive
                      ? 'bg-sky-600 text-white shadow-sm'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span className="hidden md:inline">{tab.label}</span>
                </button>
              );
            })}
          </nav>

          <div className="flex items-center space-x-2">
            <div className="flex items-center space-x-1.5 px-2.5 py-1 rounded-full bg-slate-800/80 border border-slate-700 text-xs text-slate-300">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
              <span className="truncate max-w-[100px]">{user?.username || 'Demo Admin'}</span>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}
