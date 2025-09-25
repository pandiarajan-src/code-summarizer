// Code Summarizer Frontend Configuration
// This file can be used to override default API settings

window.FRONTEND_CONFIG = {
    // API Configuration
    api: {
        // Default development settings - will be overridden by environment detection
        baseUrl: window.API_BASE_URL || 'http://127.0.0.1:8000',
        timeout: 300000, // 5 minutes
        retryAttempts: 3,
        retryDelay: 1000, // 1 second
    },

    // UI Configuration
    ui: {
        theme: 'intel-blue', // Available: 'intel-blue', 'dark', 'light'
        animations: true,
        notifications: true,
        autoScroll: true,
    },

    // File Upload Configuration
    upload: {
        maxFileSize: 50 * 1024 * 1024, // 50MB
        maxFiles: 100,
        chunkSize: 1024 * 1024, // 1MB chunks
        allowedExtensions: [
            // Programming languages
            '.py', '.js', '.ts', '.jsx', '.tsx',
            '.java', '.cpp', '.c', '.h', '.hpp',
            '.cs', '.rb', '.go', '.php', '.rs',
            '.swift', '.kt', '.scala', '.r', '.m',

            // Web technologies
            '.html', '.css', '.scss', '.sass',
            '.vue', '.svelte',

            // Configuration and data
            '.json', '.yaml', '.yml', '.xml',
            '.toml', '.ini', '.cfg',

            // Documentation
            '.md', '.rst', '.txt',

            // Archives
            '.zip'
        ]
    },

    // Development settings
    development: {
        debug: false,
        logLevel: 'info', // 'debug', 'info', 'warn', 'error'
        mockApi: false,
    }
};

// Environment-specific overrides
if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
    // Development environment
    window.FRONTEND_CONFIG.development.debug = true;
    window.FRONTEND_CONFIG.development.logLevel = 'debug';

    // Use environment-aware API URL for development
    if (!window.API_BASE_URL) {
        const port = window.API_PORT || '8000';
        window.FRONTEND_CONFIG.api.baseUrl = `http://${window.location.hostname}:${port}`;
    }
} else {
    // Production environment - use proxied API or environment variable
    window.FRONTEND_CONFIG.api.baseUrl = window.API_BASE_URL || (window.location.origin + '/api');
    window.FRONTEND_CONFIG.development.debug = false;
}

// Merge with existing API_CONFIG if it exists
if (window.API_CONFIG) {
    window.FRONTEND_CONFIG.api = {
        ...window.FRONTEND_CONFIG.api,
        ...window.API_CONFIG
    };
}