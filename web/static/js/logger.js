/**
 * Odin Structured Logging System - JavaScript Frontend Logger
 * Provides consistent, structured logging across all frontend JavaScript
 * with log levels, timestamps, context tracking, and optional backend reporting
 */

class OdinLogger {
    constructor(componentName = 'app') {
        this.componentName = componentName;
        this.logLevel = this.getConfiguredLogLevel();
        this.correlationId = this.generateCorrelationId();
        this.enableBackendLogging = false; // Can be enabled for error reporting
        this.backendEndpoint = '/api/v1/logs';

        // Log levels in order of severity
        this.levels = {
            DEBUG: 0,
            INFO: 1,
            WARN: 2,
            ERROR: 3,
            CRITICAL: 4
        };

        // Color coding for different log levels
        this.colors = {
            DEBUG: '#8b92b0',
            INFO: '#0099ff',
            WARN: '#ffa500',
            ERROR: '#ff1744',
            CRITICAL: '#ff0000'
        };

        // Emoji prefixes for better visual scanning
        this.emojis = {
            DEBUG: '🔍',
            INFO: '✅',
            WARN: '⚠️',
            ERROR: '❌',
            CRITICAL: '🚨'
        };
    }

    /**
     * Get configured log level from localStorage or default to INFO
     */
    getConfiguredLogLevel() {
        const configLevel = localStorage.getItem('odin_log_level');
        return configLevel || 'INFO';
    }

    /**
     * Set log level (DEBUG, INFO, WARN, ERROR, CRITICAL)
     */
    setLogLevel(level) {
        if (this.levels.hasOwnProperty(level)) {
            this.logLevel = level;
            localStorage.setItem('odin_log_level', level);
        }
    }

    /**
     * Generate unique correlation ID for tracking related logs
     */
    generateCorrelationId() {
        return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    }

    /**
     * Check if a log level should be output
     */
    shouldLog(level) {
        return this.levels[level] >= this.levels[this.logLevel];
    }

    /**
     * Format timestamp as ISO string
     */
    getTimestamp() {
        return new Date().toISOString();
    }

    /**
     * Core logging method
     */
    log(level, message, context = {}) {
        if (!this.shouldLog(level)) {
            return;
        }

        const timestamp = this.getTimestamp();
        const emoji = this.emojis[level];
        const color = this.colors[level];

        // Structured log data
        const logData = {
            timestamp,
            level,
            component: this.componentName,
            message,
            correlationId: this.correlationId,
            context,
            url: window.location.href,
            userAgent: navigator.userAgent
        };

        // Console output with styling
        const prefix = `${emoji} [${timestamp}] [${level}] [${this.componentName}]`;

        if (context && Object.keys(context).length > 0) {
            console.log(
                `%c${prefix}%c ${message}`,
                `color: ${color}; font-weight: bold;`,
                'color: inherit;',
                context
            );
        } else {
            console.log(
                `%c${prefix}%c ${message}`,
                `color: ${color}; font-weight: bold;`,
                'color: inherit;'
            );
        }

        // Send errors to backend if enabled
        if (this.enableBackendLogging && (level === 'ERROR' || level === 'CRITICAL')) {
            this.sendToBackend(logData);
        }

        return logData;
    }

    /**
     * Debug level logging - detailed diagnostic information
     */
    debug(message, context = {}) {
        return this.log('DEBUG', message, context);
    }

    /**
     * Info level logging - general informational messages
     */
    info(message, context = {}) {
        return this.log('INFO', message, context);
    }

    /**
     * Warning level logging - warning messages for potentially harmful situations
     */
    warn(message, context = {}) {
        return this.log('WARN', message, context);
    }

    /**
     * Error level logging - error events that might still allow the application to continue
     */
    error(message, context = {}) {
        return this.log('ERROR', message, context);
    }

    /**
     * Critical level logging - severe error events that might cause the application to abort
     */
    critical(message, context = {}) {
        return this.log('CRITICAL', message, context);
    }

    /**
     * Log operation start
     */
    operationStart(operation, context = {}) {
        return this.info(`Starting ${operation}`, { ...context, operation, phase: 'start' });
    }

    /**
     * Log operation success
     */
    operationSuccess(operation, duration = null, context = {}) {
        const ctx = { ...context, operation, phase: 'success' };
        if (duration !== null) {
            ctx.duration_ms = duration;
        }
        return this.info(`Completed ${operation}`, ctx);
    }

    /**
     * Log operation error
     */
    operationError(operation, error, context = {}) {
        const ctx = {
            ...context,
            operation,
            phase: 'error',
            error_type: error.constructor.name,
            error_message: error.message,
            stack_trace: error.stack
        };
        return this.error(`Failed ${operation}`, ctx);
    }

    /**
     * Create a child logger with additional context
     */
    child(additionalContext = {}) {
        const childLogger = new OdinLogger(this.componentName);
        childLogger.logLevel = this.logLevel;
        childLogger.correlationId = this.correlationId;
        childLogger.enableBackendLogging = this.enableBackendLogging;
        childLogger.defaultContext = { ...this.defaultContext, ...additionalContext };
        return childLogger;
    }

    /**
     * Time an operation
     */
    time(label) {
        const startTime = performance.now();
        return {
            end: () => {
                const duration = performance.now() - startTime;
                this.debug(`Timer: ${label}`, { duration_ms: duration.toFixed(2) });
                return duration;
            }
        };
    }

    /**
     * Group related logs
     */
    group(label, collapsed = false) {
        if (collapsed) {
            console.groupCollapsed(`🔸 ${label}`);
        } else {
            console.group(`🔸 ${label}`);
        }
    }

    /**
     * End log group
     */
    groupEnd() {
        console.groupEnd();
    }

    /**
     * Send log to backend for persistence/analysis
     */
    async sendToBackend(logData) {
        try {
            await fetch(this.backendEndpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(logData)
            });
        } catch (err) {
            // Fail silently to avoid logging errors about logging
            console.error('Failed to send log to backend:', err);
        }
    }

    /**
     * Enable backend error reporting
     */
    enableBackendReporting(endpoint = '/api/v1/logs') {
        this.enableBackendLogging = true;
        this.backendEndpoint = endpoint;
    }

    /**
     * Disable backend error reporting
     */
    disableBackendReporting() {
        this.enableBackendLogging = false;
    }
}

/**
 * Global logger factory
 */
const LoggerFactory = {
    loggers: {},

    /**
     * Get or create a logger for a component
     */
    getLogger(componentName) {
        if (!this.loggers[componentName]) {
            this.loggers[componentName] = new OdinLogger(componentName);
        }
        return this.loggers[componentName];
    },

    /**
     * Set global log level for all loggers
     */
    setGlobalLogLevel(level) {
        localStorage.setItem('odin_log_level', level);
        Object.values(this.loggers).forEach(logger => {
            logger.setLogLevel(level);
        });
    }
};

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { OdinLogger, LoggerFactory };
}
