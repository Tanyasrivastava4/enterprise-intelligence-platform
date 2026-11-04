import React, { useState, useEffect, useRef } from 'react';
import { Send, Bot, User, Bookmark, AlertTriangle, Layers, Sparkles, RefreshCw, ChevronRight } from 'lucide-react';
import { api } from '../services/api';
import CitationDrawer from './CitationDrawer';
import AgentTraceViewer from './AgentTraceViewer';

export default function ChatView({ mode = 'chat' }) {
  const [messages, setMessages] = useState([]);
  const [inputQuery, setInputQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [activeCitation, setActiveCitation] = useState(null);
  const [conversationId, setConversationId] = useState(null);
  const [activeMode, setActiveMode] = useState(mode); // 'rag' or 'agent'
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const handleSend = async (e) => {
    e?.preventDefault();
    if (!inputQuery.trim() || loading) return;

    const userText = inputQuery.trim();
    setInputQuery('');

    // Append user message to UI
    const tempUserMsg = {
      role: 'user',
      content: userText,
      created_at: new Date().toISOString()
    };
    setMessages((prev) => [...prev, tempUserMsg]);
    setLoading(true);

    try {
      if (activeMode === 'agent') {
        // Run multi-step agent workflow
        const agentRes = await api.runAgentTask(userText, conversationId);
        setConversationId(agentRes.conversation_id);

        const asstMsg = {
          role: 'assistant',
          content: agentRes.final_output,
          structured_report: agentRes.structured_report,
          agent_trace: agentRes.steps,
          tools_used: agentRes.tools_used,
          model_used: agentRes.model_used,
          provider_used: agentRes.provider_used,
          latency_ms: agentRes.total_latency_ms,
          total_tokens: agentRes.total_tokens,
          is_fallback: agentRes.is_fallback,
          created_at: new Date().toISOString()
        };
        setMessages((prev) => [...prev, asstMsg]);
      } else {
        // Run direct Hybrid RAG query
        const ragRes = await api.queryRAG(userText, conversationId);
        setConversationId(ragRes.conversation_id);

        const asstMsg = {
          role: 'assistant',
          content: ragRes.answer,
          citations: ragRes.citations,
          conflicts_detected: ragRes.conflicts_detected,
          is_grounded: ragRes.is_grounded,
          model_used: ragRes.model_used,
          provider_used: ragRes.provider_used,
          latency_ms: ragRes.latency_ms,
          total_tokens: ragRes.total_tokens,
          is_fallback: ragRes.is_fallback,
          created_at: new Date().toISOString()
        };
        setMessages((prev) => [...prev, asstMsg]);
      }
    } catch (err) {
      const errMsg = {
        role: 'assistant',
        content: `Error executing query: ${err.response?.data?.detail || err.message}`,
        is_error: true,
        created_at: new Date().toISOString()
      };
      setMessages((prev) => [...prev, errMsg]);
    } finally {
      setLoading(false);
    }
  };

  const handleClear = () => {
    setMessages([]);
    setConversationId(null);
  };

  return (
    <div className="max-w-5xl mx-auto flex flex-col h-[calc(100vh-140px)]">
      {/* Mode Toggle & Control Bar */}
      <div className="flex items-center justify-between pb-4 border-b border-slate-800">
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setActiveMode('rag')}
            className={`flex items-center space-x-2 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              activeMode === 'rag'
                ? 'bg-sky-600 text-white shadow-md'
                : 'bg-slate-800 text-slate-400 hover:text-white'
            }`}
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>Hybrid RAG Search</span>
          </button>
          <button
            onClick={() => setActiveMode('agent')}
            className={`flex items-center space-x-2 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              activeMode === 'agent'
                ? 'bg-amber-600 text-white shadow-md'
                : 'bg-slate-800 text-slate-400 hover:text-white'
            }`}
          >
            <Layers className="w-3.5 h-3.5" />
            <span>Autonomous Agent (Multi-Tool)</span>
          </button>
        </div>

        <button
          onClick={handleClear}
          className="text-xs text-slate-400 hover:text-slate-200 px-2.5 py-1 rounded bg-slate-850 hover:bg-slate-800 transition-colors"
        >
          New Session
        </button>
      </div>

      {/* Messages Feed */}
      <div className="flex-1 overflow-y-auto py-6 space-y-6 pr-2">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center p-6 text-slate-500 space-y-4">
            <div className="w-14 h-14 rounded-2xl bg-slate-800/80 border border-slate-700/80 flex items-center justify-center text-sky-400">
              <Bot className="w-7 h-7" />
            </div>
            <div>
              <h3 className="text-base font-semibold text-slate-200">Enterprise Intelligence Workspace</h3>
              <p className="text-xs text-slate-400 max-w-md mt-1">
                Ask questions across internal documents with source citations, or command the agent to analyze system failures and draft formal reports.
              </p>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 max-w-xl text-left text-xs font-mono">
              <button
                onClick={() => setInputQuery("What was the primary root cause of outage INC-89421 and what connection pool limit was configured?")}
                className="p-3 bg-slate-900 border border-slate-800 rounded-xl hover:border-slate-700 hover:bg-slate-850 transition-all text-slate-300"
              >
                👉 "What was the root cause of outage INC-89421 and pool limit?"
              </button>
              <button
                onClick={() => {
                  setActiveMode('agent');
                  setInputQuery("Analyze our internal technical documentation and identify the most common reasons for system failures. Provide evidence from the documents and recommend possible solutions.");
                }}
                className="p-3 bg-slate-900 border border-slate-800 rounded-xl hover:border-amber-700/60 hover:bg-slate-850 transition-all text-slate-300"
              >
                ⚡ "Analyze system failures and generate executive report"
              </button>
            </div>
          </div>
        ) : (
          messages.map((msg, idx) => {
            const isUser = msg.role === 'user';

            return (
              <div
                key={idx}
                className={`flex items-start space-x-3 ${isUser ? 'justify-end' : 'justify-start'}`}
              >
                {!isUser && (
                  <div className="w-8 h-8 rounded-lg bg-sky-600/20 border border-sky-500/30 flex items-center justify-center text-sky-400 flex-shrink-0 mt-1">
                    <Bot className="w-4 h-4" />
                  </div>
                )}

                <div
                  className={`max-w-3xl rounded-2xl p-4 sm:p-5 text-sm ${
                    isUser
                      ? 'bg-sky-600 text-white rounded-tr-sm shadow-md'
                      : 'bg-slate-900/90 border border-slate-800 text-slate-200 rounded-tl-sm shadow-xl'
                  }`}
                >
                  {/* Message Content */}
                  <div className="whitespace-pre-wrap leading-relaxed space-y-2">
                    {msg.content}
                  </div>

                  {/* Conflicting Information Warning Banner */}
                  {msg.conflicts_detected && msg.conflicts_detected.length > 0 && (
                    <div className="mt-3 p-3 rounded-xl bg-amber-950/40 border border-amber-800/80 text-amber-300 text-xs flex items-start space-x-2">
                      <AlertTriangle className="w-4 h-4 flex-shrink-0 mt-0.5 text-amber-400" />
                      <div>
                        <span className="font-semibold block">Conflicting Documentation Detected:</span>
                        <ul className="list-disc list-inside mt-1 space-y-0.5 text-amber-200">
                          {msg.conflicts_detected.map((c, i) => (
                            <li key={i}>{c}</li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  )}

                  {/* Citations Pills */}
                  {msg.citations && msg.citations.length > 0 && (
                    <div className="mt-4 pt-3 border-t border-slate-800/80 flex flex-wrap gap-2 items-center">
                      <span className="text-[11px] font-mono text-slate-400 flex items-center space-x-1">
                        <Bookmark className="w-3.5 h-3.5 text-sky-400" />
                        <span>Sources:</span>
                      </span>
                      {msg.citations.map((c, cIdx) => (
                        <button
                          key={cIdx}
                          onClick={() => setActiveCitation(c)}
                          className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-md bg-slate-800 hover:bg-slate-750 text-slate-300 hover:text-white border border-slate-700 text-xs font-mono transition-colors"
                        >
                          <span>{c.document_name}</span>
                          <span className="text-slate-500">P.{c.page_or_row}</span>
                        </button>
                      ))}
                    </div>
                  )}

                  {/* Agent Structured Report Display */}
                  {msg.structured_report?.markdown_report && (
                    <div className="mt-4 p-4 rounded-xl bg-slate-950 border border-slate-800">
                      <div className="whitespace-pre-wrap text-xs font-mono text-slate-300">
                        {msg.structured_report.markdown_report}
                      </div>
                    </div>
                  )}

                  {/* Agent Trace Execution Steps */}
                  {msg.agent_trace && (
                    <AgentTraceViewer
                      steps={msg.agent_trace}
                      toolsUsed={msg.tools_used}
                      totalLatency={msg.latency_ms}
                      totalTokens={msg.total_tokens}
                    />
                  )}

                  {/* Metadata Footer */}
                  {!isUser && (
                    <div className="mt-3 flex items-center justify-between text-[11px] font-mono text-slate-500 pt-2 border-t border-slate-800/40">
                      <span>
                        {msg.model_used} • {msg.latency_ms}ms
                        {msg.is_fallback && <span className="text-amber-400 ml-1">(Fallback Provider)</span>}
                      </span>
                      <span>{msg.total_tokens || 0} tokens</span>
                    </div>
                  )}
                </div>

                {isUser && (
                  <div className="w-8 h-8 rounded-lg bg-slate-800 border border-slate-700 flex items-center justify-center text-slate-300 flex-shrink-0 mt-1">
                    <User className="w-4 h-4" />
                  </div>
                )}
              </div>
            );
          })
        )}

        {loading && (
          <div className="flex items-center space-x-3 text-slate-400 text-xs font-mono animate-pulse pl-11">
            <RefreshCw className="w-4 h-4 animate-spin text-sky-400" />
            <span>
              {activeMode === 'agent'
                ? 'Autonomous Agent executing reasoning & tool chain...'
                : 'Searching hybrid index & synthesizing grounded answer...'}
            </span>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Bar */}
      <form onSubmit={handleSend} className="pt-4 border-t border-slate-800 flex items-center space-x-3">
        <input
          type="text"
          value={inputQuery}
          onChange={(e) => setInputQuery(e.target.value)}
          placeholder={
            activeMode === 'agent'
              ? 'Command the agent (e.g. "Identify failure causes and draft an incident report")...'
              : 'Ask any question across internal documents with verifiable citations...'
          }
          className="flex-1 bg-slate-900 border border-slate-800 rounded-xl px-4 py-3 text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-sky-500/50"
          disabled={loading}
        />
        <button
          type="submit"
          disabled={loading || !inputQuery.trim()}
          className="px-5 py-3 rounded-xl bg-sky-600 hover:bg-sky-500 disabled:opacity-50 text-white font-medium text-sm flex items-center space-x-2 transition-all shadow-md"
        >
          <span>Send</span>
          <Send className="w-4 h-4" />
        </button>
      </form>

      {/* Citation Inspector Side Drawer */}
      <CitationDrawer
        citation={activeCitation}
        onClose={() => setActiveCitation(null)}
      />
    </div>
  );
}
