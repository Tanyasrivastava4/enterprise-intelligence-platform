import React, { useState } from 'react';
import Navbar from './components/Navbar';
import ChatView from './components/ChatView';
import DocumentManager from './components/DocumentManager';
import AnalyticsView from './components/AnalyticsView';

export default function App() {
  const [activeTab, setActiveTab] = useState('chat');
  const [user] = useState({ username: 'Reviewer (Admin)', email: 'reviewer@enterprise.ai' });

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      <Navbar activeTab={activeTab} setActiveTab={setActiveTab} user={user} />

      <main className="flex-1 p-4 sm:p-6 lg:p-8 max-w-7xl w-full mx-auto">
        {activeTab === 'chat' && <ChatView mode="rag" />}
        {activeTab === 'agent' && <ChatView mode="agent" />}
        {activeTab === 'documents' && <DocumentManager />}
        {activeTab === 'analytics' && <AnalyticsView />}
      </main>

      <footer className="border-t border-slate-900 bg-slate-950 py-3 text-center text-xs text-slate-500 font-mono">
        Enterprise Intelligence Platform • AI Technical Assessment • Production Architecture
      </footer>
    </div>
  );
}
