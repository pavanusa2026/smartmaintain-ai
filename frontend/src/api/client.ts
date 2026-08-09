import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      if (window.location.pathname !== '/login') {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export default api;

export const authApi = {
  login: (email: string, password: string) =>
    api.post('/auth/login', { email, password }),
};

export const dashboardApi = {
  getStats: () => api.get('/dashboard/stats'),
};

export const machinesApi = {
  list: (params?: { status?: string; search?: string }) =>
    api.get('/machines', { params }),
  get: (id: string) => api.get(`/machines/${id}`),
  create: (data: Record<string, unknown>) => api.post('/machines', data),
  update: (id: string, data: Record<string, unknown>) =>
    api.patch(`/machines/${id}`, data),
  getReadings: (id: string, limit = 100) =>
    api.get(`/machines/${id}/readings`, { params: { limit } }),
  getPrediction: (id: string) => api.get(`/machines/${id}/prediction`),
};

export const alertsApi = {
  list: (params?: { status?: string; severity?: string; machineId?: string }) =>
    api.get('/alerts', { params }),
  update: (id: string, data: Record<string, unknown>) =>
    api.patch(`/alerts/${id}`, data),
  acknowledge: (id: string) => api.post(`/alerts/${id}/acknowledge`),
};

export const workOrdersApi = {
  list: (params?: { status?: string; machineId?: string }) =>
    api.get('/work-orders', { params }),
  create: (data: Record<string, unknown>) => api.post('/work-orders', data),
  update: (id: string, data: Record<string, unknown>) =>
    api.patch(`/work-orders/${id}`, data),
};

export const inspectionsApi = {
  list: () => api.get('/inspections'),
  get: (id: string) => api.get(`/inspections/${id}`),
  upload: (file: File, productId?: string) => {
    const form = new FormData();
    form.append('file', file);
    if (productId) form.append('productId', productId);
    return api.post('/inspections', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  review: (id: string, data: Record<string, unknown>) =>
    api.patch(`/inspections/${id}/review`, data),
};

export const assistantApi = {
  query: (question: string, machineId?: string) =>
    api.post('/assistant/query', { question, machineId }),
};

export const reportsApi = {
  getSummary: () => api.get('/reports/summary'),
};

export const feedbackApi = {
  submit: (data: Record<string, unknown>) => api.post('/feedback', data),
};
