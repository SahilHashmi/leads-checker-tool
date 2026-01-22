import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://138.226.247.175:4005/api';

console.log('[API] Initializing API client');
console.log('[API] Base URL:', API_URL);
console.log('[API] Environment:', import.meta.env.MODE);

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30 second timeout
});

// Request interceptor - add auth headers and logging
api.interceptors.request.use(
  (config) => {
    console.log(`[API Request] ${config.method?.toUpperCase()} ${config.url}`);
    
    const deviceKey = localStorage.getItem('deviceKey');
    if (deviceKey) {
      config.headers['X-Device-Key'] = deviceKey;
    }
    
    const adminToken = localStorage.getItem('adminToken');
    if (adminToken && config.url.startsWith('/admin')) {
      config.headers['Authorization'] = `Bearer ${adminToken}`;
    }
    
    return config;
  },
  (error) => {
    console.error('[API Request Error]', error);
    return Promise.reject(error);
  }
);

// Response interceptor - handle errors and logging
api.interceptors.response.use(
  (response) => {
    console.log(`[API Response] ${response.config.method?.toUpperCase()} ${response.config.url} - Status: ${response.status}`);
    return response;
  },
  (error) => {
    console.error('[API Error]', {
      url: error.config?.url,
      method: error.config?.method,
      status: error.response?.status,
      message: error.message,
      data: error.response?.data
    });
    
    // Handle specific error cases
    if (error.code === 'ECONNABORTED') {
      console.error('[API] Request timeout - server took too long to respond');
      error.message = 'Request timeout. The server is taking too long to respond.';
    } else if (error.code === 'ERR_NETWORK') {
      console.error('[API] Network error - cannot reach server');
      error.message = 'Network error. Cannot reach the server. Please check your connection.';
    } else if (!error.response) {
      console.error('[API] No response from server');
      error.message = 'No response from server. Please check if the backend is running.';
    } else if (error.response.status === 500) {
      console.error('[API] Server error:', error.response.data);
      error.message = error.response.data?.detail || 'Internal server error. Please check server logs.';
    } else if (error.response.status === 404) {
      console.error('[API] Not found:', error.config?.url);
    } else if (error.response.status === 401) {
      console.error('[API] Unauthorized - invalid credentials or token');
    }
    
    return Promise.reject(error);
  }
);

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
