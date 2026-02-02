import axios from 'axios';

// For Azure/Production: set REACT_APP_API_URL to your backend URL (e.g., https://your-backend.azurewebsites.net/api)
// For Local Development: defaults to /api (uses proxy)
const API_BASE_URL = process.env.REACT_APP_API_URL || '/api';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle auth errors
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Unauthorized - token expired or invalid
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export const amendmentAPI = {
  getAll: (params = {}) => {
    return apiClient.get('/amendments', { params });
  },

  getById: (id) => {
    return apiClient.get(`/amendments/${id}`);
  },

  getByReference: (reference) => {
    return apiClient.get(`/amendments/reference/${reference}`);
  },

  create: (data) => {
    return apiClient.post('/amendments', data);
  },

  update: (id, data) => {
    return apiClient.put(`/amendments/${id}`, data);
  },

  delete: (id) => {
    return apiClient.delete(`/amendments/${id}`);
  },

  bulkUpdate: (updates) => {
    return apiClient.post('/amendments/bulk-update', updates);
  },

  getStats: () => {
    return apiClient.get('/amendments/stats');
  },

  getVersionStats: () => {
    return apiClient.get('/amendments/version-stats');
  },

  addProgress: (id, data) => {
    return apiClient.post(`/amendments/${id}/progress`, data);
  },

  getProgress: (id) => {
    return apiClient.get(`/amendments/${id}/progress`);
  },

  linkAmendments: (id, linkedId, linkType = 'Related') => {
    return apiClient.post(`/amendments/${id}/links`, {
      linked_amendment_id: linkedId,
      link_type: linkType,
    });
  },

  unlinkAmendments: (id, linkedId) => {
    return apiClient.delete(`/amendments/${id}/links/${linkedId}`);
  },

  addApplication: (id, appData) => {
    return apiClient.post(`/amendments/${id}/applications`, appData);
  },

  getApplications: (id) => {
    return apiClient.get(`/amendments/${id}/applications`);
  },

  updateApplication: (appLinkId, appData) => {
    return apiClient.put(`/amendment-applications/${appLinkId}`, appData);
  },

  deleteApplication: (appLinkId) => {
    return apiClient.delete(`/amendment-applications/${appLinkId}`);
  },

  updateQA: (id, qaData) => {
    return apiClient.patch(`/amendments/${id}/qa`, qaData);
  },
};

export const referenceAPI = {
  getStatuses: () => {
    return apiClient.get('/reference/statuses');
  },

  getPriorities: () => {
    return apiClient.get('/reference/priorities');
  },

  getTypes: () => {
    return apiClient.get('/reference/types');
  },

  getForces: () => {
    return apiClient.get('/reference/forces');
  },

  getDevelopmentStatuses: () => {
    return apiClient.get('/reference/development-statuses');
  },

  getLinkTypes: () => {
    return apiClient.get('/reference/link-types');
  },
};

export const employeeAPI = {
  getAll: (params = {}) => {
    return apiClient.get('/employees', { params });
  },

  getById: (id) => {
    return apiClient.get(`/employees/${id}`);
  },

  create: (data) => {
    return apiClient.post('/employees', data);
  },

  update: (id, data) => {
    return apiClient.put(`/employees/${id}`, data);
  },

  delete: (id) => {
    return apiClient.delete(`/employees/${id}`);
  },
};

export const applicationAPI = {
  getAll: (params = {}) => {
    return apiClient.get('/applications', { params });
  },

  getById: (id) => {
    return apiClient.get(`/applications/${id}`);
  },

  create: (data) => {
    return apiClient.post('/applications', data);
  },

  update: (id, data) => {
    return apiClient.put(`/applications/${id}`, data);
  },

  delete: (id) => {
    return apiClient.delete(`/applications/${id}`);
  },

  getVersions: (id, params = {}) => {
    return apiClient.get(`/applications/${id}/versions`, { params });
  },

  createVersion: (id, data) => {
    return apiClient.post(`/applications/${id}/versions`, data);
  },
};

export const versionAPI = {
  getById: (id) => {
    return apiClient.get(`/versions/${id}`);
  },

  update: (id, data) => {
    return apiClient.put(`/versions/${id}`, data);
  },

  delete: (id) => {
    return apiClient.delete(`/versions/${id}`);
  },
};

export const documentAPI = {
  upload: (amendmentId, formData) => {
    return apiClient.post(`/amendments/${amendmentId}/documents`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },

  getAll: (amendmentId) => {
    return apiClient.get(`/amendments/${amendmentId}/documents`);
  },

  download: (documentId) => {
    return apiClient.get(`/documents/${documentId}/download`, {
      responseType: 'blob',
    });
  },

  delete: (documentId) => {
    return apiClient.delete(`/documents/${documentId}`);
  },
};

export default apiClient;
