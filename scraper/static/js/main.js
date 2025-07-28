/**
 * Mercado Brasil API - Main JavaScript File
 * Handles global functionality, API integration, and utilities
 */

// Global configuration
const CONFIG = {
    API_BASE_URL: '/api/v1',
    WEBSOCKET_URL: '/socket.io',
    STORAGE_KEY: 'mercado_brasil_api_key',
    DEFAULT_TIMEOUT: 10000,
    RETRY_ATTEMPTS: 3
};

// Global state management
const AppState = {
    apiKey: null,
    socket: null,
    isConnected: false,
    subscriptions: [],
    currentUser: null,
    settings: {
        theme: 'light',
        language: 'pt-BR',
        refreshInterval: 5000
    }
};

// Utility functions
const Utils = {
    /**
     * Format number as Brazilian currency
     */
    formatCurrency(value, currency = 'BRL') {
        return new Intl.NumberFormat('pt-BR', {
            style: 'currency',
            currency: currency
        }).format(value);
    },

    /**
     * Format percentage
     */
    formatPercentage(value, decimals = 2) {
        return new Intl.NumberFormat('pt-BR', {
            style: 'percent',
            minimumFractionDigits: decimals,
            maximumFractionDigits: decimals
        }).format(value / 100);
    },

    /**
     * Format large numbers with abbreviations
     */
    formatLargeNumber(value) {
        if (value >= 1e9) {
            return (value / 1e9).toFixed(1) + 'B';
        } else if (value >= 1e6) {
            return (value / 1e6).toFixed(1) + 'M';
        } else if (value >= 1e3) {
            return (value / 1e3).toFixed(1) + 'K';
        }
        return value.toString();
    },

    /**
     * Format date
     */
    formatDate(date, options = {}) {
        const defaultOptions = {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        };
        
        return new Intl.DateTimeFormat('pt-BR', { ...defaultOptions, ...options })
            .format(new Date(date));
    },

    /**
     * Debounce function
     */
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },

    /**
     * Show toast notification
     */
    showToast(message, type = 'info', duration = 3000) {
        const toastContainer = document.getElementById('toast-container') || this.createToastContainer();
        
        const toast = document.createElement('div');
        toast.className = `toast align-items-center text-white bg-${type} border-0`;
        toast.setAttribute('role', 'alert');
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">${message}</div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        `;
        
        toastContainer.appendChild(toast);
        
        const bsToast = new bootstrap.Toast(toast, { autohide: true, delay: duration });
        bsToast.show();
        
        toast.addEventListener('hidden.bs.toast', () => {
            toast.remove();
        });
    },

    /**
     * Create toast container if it doesn't exist
     */
    createToastContainer() {
        const container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'toast-container position-fixed top-0 end-0 p-3';
        container.style.zIndex = '1055';
        document.body.appendChild(container);
        return container;
    },

    /**
     * Copy text to clipboard
     */
    async copyToClipboard(text) {
        try {
            await navigator.clipboard.writeText(text);
            this.showToast('Copiado para a área de transferência', 'success');
            return true;
        } catch (err) {
            console.error('Erro ao copiar:', err);
            this.showToast('Erro ao copiar texto', 'danger');
            return false;
        }
    },

    /**
     * Validate ticker format
     */
    validateTicker(ticker) {
        const pattern = /^(\^[A-Z]{3,4}|[A-Z]{4}\d{1,2})$/;
        return pattern.test(ticker.toUpperCase());
    },

    /**
     * Get color for percentage change
     */
    getChangeColor(value) {
        if (value > 0) return 'text-success';
        if (value < 0) return 'text-danger';
        return 'text-muted';
    },

    /**
     * Get icon for percentage change
     */
    getChangeIcon(value) {
        if (value > 0) return 'fas fa-arrow-up';
        if (value < 0) return 'fas fa-arrow-down';
        return 'fas fa-minus';
    }
};

// API Manager
const APIManager = {
    /**
     * Make authenticated API request
     */
    async request(endpoint, options = {}) {
        const apiKey = AppState.apiKey || localStorage.getItem(CONFIG.STORAGE_KEY);
        
        if (!apiKey) {
            throw new Error('API Key não configurada');
        }

        const defaultOptions = {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${apiKey}`,
                'Content-Type': 'application/json'
            },
            timeout: CONFIG.DEFAULT_TIMEOUT
        };

        const finalOptions = { ...defaultOptions, ...options };
        const url = `${CONFIG.API_BASE_URL}${endpoint}`;

        try {
            const response = await fetch(url, finalOptions);
            
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.message || `HTTP ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('API Request Error:', error);
            throw error;
        }
    },

    /**
     * Get company data
     */
    async getCompany(cvmCode) {
        return await this.request(`/companies/${cvmCode}`);
    },

    /**
     * Get quotes
     */
    async getQuotes(tickers) {
        const tickersParam = Array.isArray(tickers) ? tickers.join(',') : tickers;
        return await this.request(`/quotes?tickers=${tickersParam}`);
    },

    /**
     * Get historical data
     */
    async getHistoricalData(ticker, period = '1y', interval = '1d') {
        return await this.request(`/quotes/${ticker}/history?period=${period}&interval=${interval}`);
    },

    /**
     * Get news
     */
    async getNews(params = {}) {
        const queryString = new URLSearchParams(params).toString();
        return await this.request(`/news${queryString ? '?' + queryString : ''}`);
    },

    /**
     * Get macroeconomic indicators
     */
    async getMacroIndicators(indicator = null) {
        const endpoint = indicator ? `/macroeconomics/indicators?indicator=${indicator}` : '/macroeconomics/indicators';
        return await this.request(endpoint);
    },

    /**
     * Get market indices
     */
    async getIndices() {
        return await this.request('/indices');
    }
};

// WebSocket Manager
const WebSocketManager = {
    socket: null,
    reconnectAttempts: 0,
    maxReconnectAttempts: 5,
    reconnectDelay: 1000,

    /**
     * Connect to WebSocket
     */
    connect() {
        const apiKey = AppState.apiKey || localStorage.getItem(CONFIG.STORAGE_KEY);
        
        if (!apiKey) {
            Utils.showToast('API Key necessária para WebSocket', 'warning');
            return;
        }

        if (this.socket) {
            this.disconnect();
        }

        try {
            this.socket = io();
            this.setupEventHandlers();
            AppState.socket = this.socket;
        } catch (error) {
            console.error('WebSocket connection error:', error);
            Utils.showToast('Erro ao conectar WebSocket', 'danger');
        }
    },

    /**
     * Setup WebSocket event handlers
     */
    setupEventHandlers() {
        if (!this.socket) return;

        this.socket.on('connect', () => {
            console.log('WebSocket connected');
            AppState.isConnected = true;
            this.reconnectAttempts = 0;
            
            // Authenticate
            const apiKey = AppState.apiKey || localStorage.getItem(CONFIG.STORAGE_KEY);
            this.socket.emit('authenticate', { api_key: apiKey });
            
            this.onConnected();
        });

        this.socket.on('disconnect', () => {
            console.log('WebSocket disconnected');
            AppState.isConnected = false;
            this.onDisconnected();
            this.scheduleReconnect();
        });

        this.socket.on('authenticated', (data) => {
            console.log('WebSocket authenticated:', data);
            Utils.showToast('WebSocket conectado com sucesso', 'success');
            this.onAuthenticated(data);
        });

        this.socket.on('error', (data) => {
            console.error('WebSocket error:', data);
            Utils.showToast(`WebSocket erro: ${data.message}`, 'danger');
        });

        this.socket.on('quote_update', (data) => {
            this.onQuoteUpdate(data);
        });

        this.socket.on('orderbook_update', (data) => {
            this.onOrderBookUpdate(data);
        });

        this.socket.on('trade_update', (data) => {
            this.onTradeUpdate(data);
        });
    },

    /**
     * Disconnect WebSocket
     */
    disconnect() {
        if (this.socket) {
            this.socket.disconnect();
            this.socket = null;
            AppState.socket = null;
            AppState.isConnected = false;
        }
    },

    /**
     * Subscribe to quotes
     */
    subscribeQuotes(tickers) {
        if (!this.socket || !AppState.isConnected) {
            Utils.showToast('WebSocket não conectado', 'warning');
            return;
        }

        this.socket.emit('subscribe_quotes', { tickers });
        AppState.subscriptions.push(...tickers.map(ticker => ({ type: 'quotes', ticker })));
    },

    /**
     * Unsubscribe from updates
     */
    unsubscribe(type, ticker = null) {
        if (!this.socket) return;

        this.socket.emit('unsubscribe', { type, ticker });
        
        // Remove from local subscriptions
        AppState.subscriptions = AppState.subscriptions.filter(sub => {
            if (ticker) {
                return !(sub.type === type && sub.ticker === ticker);
            } else {
                return sub.type !== type;
            }
        });
    },

    /**
     * Schedule reconnection
     */
    scheduleReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            setTimeout(() => {
                this.reconnectAttempts++;
                console.log(`Reconnecting WebSocket (attempt ${this.reconnectAttempts})`);
                this.connect();
            }, this.reconnectDelay * this.reconnectAttempts);
        }
    },

    // Event callbacks (can be overridden)
    onConnected() {
        document.dispatchEvent(new CustomEvent('websocket:connected'));
    },

    onDisconnected() {
        document.dispatchEvent(new CustomEvent('websocket:disconnected'));
    },

    onAuthenticated(data) {
        document.dispatchEvent(new CustomEvent('websocket:authenticated', { detail: data }));
    },

    onQuoteUpdate(data) {
        document.dispatchEvent(new CustomEvent('websocket:quote_update', { detail: data }));
    },

    onOrderBookUpdate(data) {
        document.dispatchEvent(new CustomEvent('websocket:orderbook_update', { detail: data }));
    },

    onTradeUpdate(data) {
        document.dispatchEvent(new CustomEvent('websocket:trade_update', { detail: data }));
    }
};

// Chart Manager
const ChartManager = {
    charts: new Map(),
    defaultColors: [
        '#0d6efd', '#198754', '#ffc107', '#dc3545', '#0dcaf0',
        '#6f42c1', '#fd7e14', '#20c997', '#e83e8c', '#6c757d'
    ],

    /**
     * Create line chart
     */
    createLineChart(canvasId, data, options = {}) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return null;

        const defaultOptions = {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true,
                    position: 'top'
                }
            },
            scales: {
                x: {
                    display: true,
                    title: {
                        display: true,
                        text: 'Data'
                    }
                },
                y: {
                    display: true,
                    title: {
                        display: true,
                        text: 'Valor'
                    }
                }
            }
        };

        const chart = new Chart(ctx, {
            type: 'line',
            data,
            options: { ...defaultOptions, ...options }
        });

        this.charts.set(canvasId, chart);
        return chart;
    },

    /**
     * Create candlestick chart
     */
    createCandlestickChart(canvasId, data, options = {}) {
        // Note: This would require Chart.js with candlestick plugin
        // For now, we'll create a line chart as fallback
        return this.createLineChart(canvasId, data, options);
    },

    /**
     * Update chart data
     */
    updateChart(canvasId, newData) {
        const chart = this.charts.get(canvasId);
        if (!chart) return;

        chart.data = newData;
        chart.update();
    },

    /**
     * Destroy chart
     */
    destroyChart(canvasId) {
        const chart = this.charts.get(canvasId);
        if (chart) {
            chart.destroy();
            this.charts.delete(canvasId);
        }
    },

    /**
     * Destroy all charts
     */
    destroyAllCharts() {
        this.charts.forEach(chart => chart.destroy());
        this.charts.clear();
    }
};

// Global functions
function saveApiKey() {
    const apiKeyInput = document.getElementById('apiKeyInput');
    const apiKey = apiKeyInput.value.trim();
    
    if (!apiKey) {
        Utils.showToast('Insira uma API Key válida', 'warning');
        return;
    }
    
    localStorage.setItem(CONFIG.STORAGE_KEY, apiKey);
    AppState.apiKey = apiKey;
    
    // Close modal
    const modal = bootstrap.Modal.getInstance(document.getElementById('apiKeyModal'));
    if (modal) {
        modal.hide();
    }
    
    Utils.showToast('API Key salva com sucesso', 'success');
    
    // Trigger page refresh or data reload
    if (typeof refreshData === 'function') {
        refreshData();
    }
}

function clearApiKey() {
    localStorage.removeItem(CONFIG.STORAGE_KEY);
    AppState.apiKey = null;
    Utils.showToast('API Key removida', 'info');
}

function getStoredApiKey() {
    return localStorage.getItem(CONFIG.STORAGE_KEY);
}

// Initialize application
document.addEventListener('DOMContentLoaded', function() {
    // Load stored API key
    AppState.apiKey = getStoredApiKey();
    
    // Update API key input if exists
    const apiKeyInput = document.getElementById('apiKeyInput');
    if (apiKeyInput && AppState.apiKey) {
        apiKeyInput.value = AppState.apiKey;
    }
    
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Initialize popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
    
    // Create toast container
    Utils.createToastContainer();
    
    console.log('Mercado Brasil API initialized');
});

// Handle page visibility changes
document.addEventListener('visibilitychange', function() {
    if (document.visibilityState === 'visible') {
        // Page became visible, reconnect WebSocket if needed
        if (AppState.socket && !AppState.isConnected) {
            WebSocketManager.connect();
        }
    } else {
        // Page became hidden, optionally disconnect WebSocket to save resources
        // WebSocketManager.disconnect();
    }
});

// Handle window beforeunload
window.addEventListener('beforeunload', function() {
    // Clean up WebSocket connections
    WebSocketManager.disconnect();
    
    // Destroy charts to free memory
    ChartManager.destroyAllCharts();
});

// Export global objects for use in other scripts
window.MercadoBrasilAPI = {
    Utils,
    APIManager,
    WebSocketManager,
    ChartManager,
    AppState,
    CONFIG
};

// Legacy function support
window.saveApiKey = saveApiKey;
window.clearApiKey = clearApiKey;
window.getStoredApiKey = getStoredApiKey;
