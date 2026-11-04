import axios from 'axios';

const API_BASE = '/api/v1';

const apiClient = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json'
  }
});

// Attach JWT token automatically
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const api = {
  // Auth
  login: async (username_or_email, password) => {
    const res = await apiClient.post('/auth/login', { username_or_email, password });
    return res.data;
  },
  register: async (email, username, password, full_name) => {
    const res = await apiClient.post('/auth/register', { email, username, password, full_name });
    return res.data;
  },
  getMe: async () => {
    const res = await apiClient.get('/auth/me');
    return res.data;
  },

  // Documents
  getDocuments: async () => {
    const res = await apiClient.get('/documents');
    return res.data;
  },
  uploadDocument: async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    const res = await apiClient.post('/documents/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return res.data;
  },
  deleteDocument: async (docId) => {
    const res = await apiClient.delete(`/documents/${docId}`);
    return res.data;
  },

  // Chat & RAG
  queryRAG: async (query, conversationId = null, documentIds = null, hybrid = true) => {
    const res = await apiClient.post('/chat/query', {
      query,
      conversation_id: conversationId,
      document_ids: documentIds,
      hybrid_search: hybrid
    });
    return res.data;
  },
  getConversations: async () => {
    const res = await apiClient.get('/chat/conversations');
    return res.data;
  },
  getMessages: async (conversationId) => {
    const res = await apiClient.get(`/chat/conversations/${conversationId}/messages`);
    return res.data;
  },

  // Agent
  runAgentTask: async (task, conversationId = null, maxSteps = 6) => {
    const res = await apiClient.post('/agent/run', {
      task,
      conversation_id: conversationId,
      max_steps: maxSteps
    });
    return res.data;
  },

  // Analytics
  getAnalyticsSummary: async () => {
    const res = await apiClient.get('/analytics/summary');
    return res.data;
  },
  getTelemetryLogs: async (limit = 30) => {
    const res = await apiClient.get(`/analytics/logs?limit=${limit}`);
    return res.data;
  }
};
