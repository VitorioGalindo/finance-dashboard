// frontend/src/services/api.js
import axios from 'axios';

// URL base da API - ajuste conforme necessário
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5001/api';

// Configuração do axios
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor para tratamento de erros
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error);
    return Promise.reject(error);
  }
);

// Serviços de API
export const apiService = {
  // Empresas
  getCompanies: async (page = 1, perPage = 50, search = '') => {
    const params = new URLSearchParams();
    if (page) params.append('page', page);
    if (perPage) params.append('per_page', perPage);
    if (search) params.append('search', search);
    
    const response = await api.get(`/companies?${params}`);
    return response.data;
  },

  getCompany: async (id) => {
    const response = await api.get(`/companies/${id}`);
    return response.data;
  },

  getCompanyFinancials: async (id) => {
    const response = await api.get(`/companies/${id}/financials`);
    return response.data;
  },

  // Mercado
  getMarketOverview: async () => {
    const response = await api.get('/market/overview');
    return response.data;
  },

  getMarketSectors: async () => {
    const response = await api.get('/market/sectors');
    return response.data;
  },

  getTickers: async (page = 1, perPage = 50, search = '') => {
    const params = new URLSearchParams();
    if (page) params.append('page', page);
    if (perPage) params.append('per_page', perPage);
    if (search) params.append('search', search);
    
    const response = await api.get(`/market/tickers?${params}`);
    return response.data;
  },

  getTickerQuotes: async (ticker) => {
    const response = await api.get(`/market/quotes/${ticker}`);
    return response.data;
  },

  // Insider Trading
  getInsiderTransactions: async (limit = 20, cvmCode = null) => {
    const params = new URLSearchParams();
    if (limit) params.append('limit', limit);
    if (cvmCode) params.append('cvm_code', cvmCode);
    
    const response = await api.get(`/market/insider-transactions?${params}`);
    return response.data;
  },

  // Notícias
  getNews: async (limit = 10, ticker = null) => {
    const params = new URLSearchParams();
    if (limit) params.append('limit', limit);
    if (ticker) params.append('ticker', ticker);
    
    const response = await api.get(`/market/news?${params}`);
    return response.data;
  },

  // Dados Financeiros
  getFinancialsSummary: async () => {
    const response = await api.get('/financials/summary');
    return response.data;
  },

  getCompaniesWithFinancials: async (page = 1, perPage = 20, year = null) => {
    const params = new URLSearchParams();
    if (page) params.append('page', page);
    if (perPage) params.append('per_page', perPage);
    if (year) params.append('year', year);
    
    const response = await api.get(`/financials/companies?${params}`);
    return response.data;
  },

  getCompanyMetrics: async (companyId) => {
    const response = await api.get(`/financials/metrics/${companyId}`);
    return response.data;
  },

  // Health Check
  healthCheck: async () => {
    const response = await api.get('/health', { baseURL: 'http://localhost:5001' });
    return response.data;
  }
};

export default apiService;

