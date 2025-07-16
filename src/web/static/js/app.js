// TESTIA AI Agent - Main JavaScript

class TestiaApp {
    constructor() {
        this.apiBase = '/api';
        this.init();
    }

    init() {
        // Initialize on DOM load
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.onReady());
        } else {
            this.onReady();
        }
    }

    onReady() {
        this.setupGlobalHandlers();
        this.checkSystemStatus();
    }

    setupGlobalHandlers() {
        // Global error handler
        window.addEventListener('error', (event) => {
            console.error('Global error:', event.error);
            this.showNotification('Ha ocurrido un error inesperado', 'danger');
        });

        // Handle unhandled promise rejections
        window.addEventListener('unhandledrejection', (event) => {
            console.error('Unhandled promise rejection:', event.reason);
            this.showNotification('Error de conexión', 'warning');
        });

        // Setup navigation highlighting
        this.highlightActiveNavigation();
    }

    highlightActiveNavigation() {
        const currentPath = window.location.pathname;
        const navLinks = document.querySelectorAll('.navbar-nav .nav-link');
        
        navLinks.forEach(link => {
            if (link.getAttribute('href') === currentPath) {
                link.classList.add('active');
            }
        });
    }

    async checkSystemStatus() {
        try {
            const response = await fetch(`${this.apiBase}/status`);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            const status = await response.json();
            this.updateStatusIndicators(status);
            
        } catch (error) {
            console.error('Error checking system status:', error);
            this.updateStatusIndicators(null);
        }
    }

    updateStatusIndicators(status) {
        // Update various status indicators throughout the app
        const indicators = document.querySelectorAll('[data-status-indicator]');
        
        indicators.forEach(indicator => {
            const type = indicator.dataset.statusIndicator;
            
            if (status) {
                switch (type) {
                    case 'system':
                        indicator.textContent = 'Activo';
                        indicator.className = 'badge bg-success';
                        break;
                    case 'agents':
                        indicator.textContent = status.agents?.enabled_agents || 0;
                        break;
                    case 'models':
                        indicator.textContent = status.models || 0;
                        break;
                    case 'mcp':
                        indicator.textContent = status.mcp_connections || 0;
                        break;
                }
            } else {
                if (type === 'system') {
                    indicator.textContent = 'Error';
                    indicator.className = 'badge bg-danger';
                }
            }
        });
    }

    showNotification(message, type = 'info', duration = 5000) {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
        notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
        
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        // Add to page
        document.body.appendChild(notification);

        // Auto remove after duration
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, duration);
    }

    async apiCall(endpoint, options = {}) {
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
            }
        };

        const config = { ...defaultOptions, ...options };
        
        try {
            const response = await fetch(`${this.apiBase}${endpoint}`, config);
            
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || `HTTP ${response.status}`);
            }
            
            return await response.json();
            
        } catch (error) {
            console.error(`API call failed: ${endpoint}`, error);
            throw error;
        }
    }

    formatTimestamp(timestamp) {
        const date = new Date(timestamp);
        return date.toLocaleString('es-ES', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    }

    formatFileSize(bytes) {
        const sizes = ['B', 'KB', 'MB', 'GB'];
        if (bytes === 0) return '0 B';
        
        const i = Math.floor(Math.log(bytes) / Math.log(1024));
        return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
    }

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
    }

    // Loading states
    showLoading(element, text = 'Cargando...') {
        const spinner = document.createElement('div');
        spinner.className = 'text-center p-3';
        spinner.innerHTML = `
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">${text}</span>
            </div>
            <p class="mt-2 text-muted">${text}</p>
        `;
        
        element.innerHTML = '';
        element.appendChild(spinner);
    }

    hideLoading(element) {
        const spinner = element.querySelector('.spinner-border');
        if (spinner) {
            spinner.closest('.text-center').remove();
        }
    }

    // Form helpers
    collectFormData(form) {
        const formData = new FormData(form);
        const data = {};
        
        for (let [key, value] of formData.entries()) {
            if (data[key]) {
                // Handle multiple values (like checkboxes)
                if (Array.isArray(data[key])) {
                    data[key].push(value);
                } else {
                    data[key] = [data[key], value];
                }
            } else {
                data[key] = value;
            }
        }
        
        return data;
    }

    validateForm(form) {
        const requiredFields = form.querySelectorAll('[required]');
        let isValid = true;
        
        requiredFields.forEach(field => {
            if (!field.value.trim()) {
                field.classList.add('is-invalid');
                isValid = false;
            } else {
                field.classList.remove('is-invalid');
            }
        });
        
        return isValid;
    }

    // WebSocket helpers
    createWebSocket(endpoint) {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}${endpoint}`;
        
        const ws = new WebSocket(wsUrl);
        
        ws.onopen = () => {
            console.log(`WebSocket connected: ${endpoint}`);
        };
        
        ws.onclose = (event) => {
            console.log(`WebSocket disconnected: ${endpoint}`, event);
            if (!event.wasClean) {
                this.showNotification('Conexión perdida. Reintentando...', 'warning');
            }
        };
        
        ws.onerror = (error) => {
            console.error(`WebSocket error: ${endpoint}`, error);
            this.showNotification('Error de conexión WebSocket', 'danger');
        };
        
        return ws;
    }

    // Local storage helpers
    saveToStorage(key, data) {
        try {
            localStorage.setItem(key, JSON.stringify(data));
        } catch (error) {
            console.error('Error saving to localStorage:', error);
        }
    }

    loadFromStorage(key, defaultValue = null) {
        try {
            const item = localStorage.getItem(key);
            return item ? JSON.parse(item) : defaultValue;
        } catch (error) {
            console.error('Error loading from localStorage:', error);
            return defaultValue;
        }
    }

    removeFromStorage(key) {
        try {
            localStorage.removeItem(key);
        } catch (error) {
            console.error('Error removing from localStorage:', error);
        }
    }

    // Theme management
    initTheme() {
        const savedTheme = this.loadFromStorage('theme', 'light');
        this.setTheme(savedTheme);
    }

    setTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        this.saveToStorage('theme', theme);
        
        // Update theme toggle if it exists
        const themeToggle = document.getElementById('theme-toggle');
        if (themeToggle) {
            themeToggle.checked = theme === 'dark';
        }
    }

    toggleTheme() {
        const currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
        const newTheme = currentTheme === 'light' ? 'dark' : 'light';
        this.setTheme(newTheme);
    }
}

// Initialize app
const testiaApp = new TestiaApp();

// Make app globally available
window.TestiaApp = testiaApp;

// Export for modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = TestiaApp;
}
