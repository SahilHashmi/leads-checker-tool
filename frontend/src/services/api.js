import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || '/api';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add device key to requests
api.interceptors.request.use((config) => {
  const deviceKey = localStorage.getItem('deviceKey');
  if (deviceKey) {
    config.headers['X-Device-Key'] = deviceKey;
  }
  
  const adminToken = localStorage.getItem('adminToken');
  if (adminToken && config.url.startsWith('/admin')) {
    config.headers['Authorization'] = `Bearer ${adminToken}`;
  }
  
  return config;
});

// Auth API
export const authApi = {
  verifyKey: (deviceKey) => 
    api.post('/auth/verify-key', { device_key: deviceKey }),
  
  adminLogin: (username, password) =>
    api.post('/auth/admin/login', { username, password }),
};

// Leads API
export const leadsApi = {
  upload: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/leads/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  
  getTaskStatus: (taskId) =>
    api.get(`/leads/task-status/${taskId}`),
  
  downloadResult: (taskId) =>
    api.get(`/leads/download-result/${taskId}`, { responseType: 'blob' }),
};

// Admin API
export const adminApi = {
  generateKey: () =>
    api.post('/admin/generate-key'),
  
  getKeys: () =>
    api.get('/admin/keys'),
  
  updateKey: (keyId, status) =>
    api.patch(`/admin/keys/${keyId}`, { status }),
  
  deleteKey: (keyId) =>
    api.delete(`/admin/keys/${keyId}`),
  
  getLeadsByDate: (fromDate, toDate) =>
    api.get('/admin/leads-by-date', {
      params: { from_date: fromDate, to_date: toDate },
      responseType: 'blob',
    }),
  
  getStats: () =>
    api.get('/admin/stats'),
};

export default api;
