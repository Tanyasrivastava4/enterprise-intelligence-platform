import React, { useState, useEffect } from 'react';
import { UploadCloud, File, Trash2, CheckCircle2, Clock, AlertCircle, RefreshCw, FileText } from 'lucide-react';
import { api } from '../services/api';

export default function DocumentManager() {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const [message, setMessage] = useState(null);

  const fetchDocs = async () => {
    try {
      setLoading(true);
      const data = await api.getDocuments();
      setDocuments(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDocs();
    const interval = setInterval(fetchDocs, 4000);
    return () => clearInterval(interval);
  }, []);

  const handleFileUpload = async (file) => {
    if (!file) return;
    try {
      setUploading(true);
      setMessage(null);
      const res = await api.uploadDocument(file);
      setMessage({
        type: res.is_duplicate ? 'info' : 'success',
        text: res.message
      });
      fetchDocs();
    } catch (err) {
      setMessage({
        type: 'error',
        text: err.response?.data?.detail || 'Failed to upload document.'
      });
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (docId, filename) => {
    if (!window.confirm(`Delete document '${filename}' and all vector embeddings?`)) return;
    try {
      await api.deleteDocument(docId);
      fetchDocs();
    } catch (err) {
      alert('Failed to delete document');
    }
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileUpload(e.dataTransfer.files[0]);
    }
  };

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white tracking-tight">Document Intelligence Pipeline</h2>
          <p className="text-sm text-slate-400">
            Multi-format ingestion (PDF, CSV, Markdown, TXT) with SHA-256 deduplication and hybrid vector indexing.
          </p>
        </div>
        <button
          onClick={fetchDocs}
          className="flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium transition-colors self-start sm:self-auto"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh Status</span>
        </button>
      </div>

      {message && (
        <div
          className={`p-3 rounded-xl border text-xs flex items-center space-x-2 ${
            message.type === 'success'
              ? 'bg-emerald-950/40 border-emerald-800 text-emerald-300'
              : message.type === 'info'
              ? 'bg-sky-950/40 border-sky-800 text-sky-300'
              : 'bg-rose-950/40 border-rose-800 text-rose-300'
          }`}
        >
          <CheckCircle2 className="w-4 h-4 flex-shrink-0" />
          <span>{message.text}</span>
        </div>
      )}

      {/* Drag & Drop Upload Zone */}
      <div
        onDragEnter={handleDrag}
        onDragOver={handleDrag}
        onDragLeave={handleDrag}
        onDrop={handleDrop}
        className={`relative border-2 border-dashed rounded-2xl p-8 text-center transition-all ${
          dragActive
            ? 'border-sky-500 bg-sky-950/20'
            : 'border-slate-800 hover:border-slate-700 bg-slate-900/40'
        }`}
      >
        <input
          type="file"
          id="file-upload"
          accept=".pdf,.txt,.md,.csv"
          onChange={(e) => handleFileUpload(e.target.files[0])}
          className="hidden"
          disabled={uploading}
        />
        <label htmlFor="file-upload" className="cursor-pointer flex flex-col items-center">
          <div className="w-12 h-12 rounded-2xl bg-sky-500/10 border border-sky-500/20 flex items-center justify-center text-sky-400 mb-3">
            <UploadCloud className="w-6 h-6" />
          </div>
          <span className="text-sm font-semibold text-slate-200">
            {uploading ? 'Processing upload...' : 'Click to upload or drag & drop documents'}
          </span>
          <span className="text-xs text-slate-500 mt-1">
            Supported Formats: PDF, Markdown (.md), CSV, Plain Text (.txt) — Max 25MB
          </span>
        </label>
      </div>

      {/* Documents List */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
        <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between">
          <span className="font-semibold text-slate-200 text-sm">
            Ingested Enterprise Documents ({documents.length})
          </span>
        </div>

        {documents.length === 0 ? (
          <div className="p-8 text-center text-slate-500 text-sm">
            No documents uploaded yet. Upload architecture specs, post-mortems, or support logs above.
          </div>
        ) : (
          <div className="divide-y divide-slate-800/60">
            {documents.map((doc) => {
              const isIndexed = doc.status === 'INDEXED';
              const isFailed = doc.status === 'FAILED';
              const isProcessing = doc.status === 'PROCESSING' || doc.status === 'PENDING';

              return (
                <div key={doc.id} className="p-4 sm:px-6 flex items-center justify-between hover:bg-slate-850/40 transition-colors">
                  <div className="flex items-center space-x-3 min-w-0">
                    <div className="w-9 h-9 rounded-lg bg-slate-800 flex items-center justify-center text-slate-400 flex-shrink-0">
                      <FileText className="w-4 h-4 text-sky-400" />
                    </div>
                    <div className="min-w-0">
                      <p className="text-sm font-medium text-white truncate max-w-xs sm:max-w-md">{doc.filename}</p>
                      <div className="flex items-center space-x-3 text-xs text-slate-500 mt-0.5 font-mono">
                        <span>{doc.file_type.toUpperCase()}</span>
                        <span>•</span>
                        <span>{(doc.file_size_bytes / 1024).toFixed(1)} KB</span>
                        <span>•</span>
                        <span>{doc.chunk_count} Chunks</span>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center space-x-4">
                    <div className="flex items-center space-x-1.5">
                      {isIndexed && (
                        <span className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                          <CheckCircle2 className="w-3.5 h-3.5" />
                          <span>Indexed</span>
                        </span>
                      )}
                      {isProcessing && (
                        <span className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-full text-xs font-medium bg-sky-500/10 text-sky-400 border border-sky-500/30 animate-pulse">
                          <Clock className="w-3.5 h-3.5" />
                          <span>Processing</span>
                        </span>
                      )}
                      {isFailed && (
                        <span className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-full text-xs font-medium bg-rose-500/10 text-rose-400 border border-rose-500/30">
                          <AlertCircle className="w-3.5 h-3.5" />
                          <span>Failed</span>
                        </span>
                      )}
                    </div>

                    <button
                      onClick={() => handleDelete(doc.id, doc.filename)}
                      className="p-1.5 text-slate-400 hover:text-rose-400 hover:bg-slate-800 rounded-lg transition-colors"
                      title="Delete document and remove embeddings"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
