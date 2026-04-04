/**
 * Error logging utility with correlation IDs
 * 
 * Provides structured error logging for debugging and monitoring
 */

export interface ErrorLog {
  correlationId: string;
  timestamp: string;
  errorType: string;
  message: string;
  stack?: string;
  context?: Record<string, any>;
  userAgent?: string;
}

// Simple UUID generator
function generateUUID(): string {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
    const r = Math.random() * 16 | 0;
    const v = c === 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
  });
}

class ErrorLogger {
  private logs: ErrorLog[] = [];
  private maxLogs = 100; // Keep last 100 errors in memory

  /**
   * Log an error with correlation ID
   */
  logError(
    error: Error | string,
    context?: Record<string, any>
  ): string {
    const correlationId = generateUUID();
    const errorLog: ErrorLog = {
      correlationId,
      timestamp: new Date().toISOString(),
      errorType: error instanceof Error ? error.name : 'Error',
      message: error instanceof Error ? error.message : error,
      stack: error instanceof Error ? error.stack : undefined,
      context,
      userAgent: typeof window !== 'undefined' ? window.navigator.userAgent : undefined,
    };

    // Add to in-memory logs
    this.logs.push(errorLog);
    if (this.logs.length > this.maxLogs) {
      this.logs.shift();
    }

    // Log to console in development
    if (process.env.NODE_ENV === 'development') {
      console.error('[Error Logger]', {
        correlationId,
        message: errorLog.message,
        context,
        stack: errorLog.stack,
      });
    }

    // In production, you would send this to a logging service
    // e.g., Sentry, LogRocket, CloudWatch, etc.
    if (process.env.NODE_ENV === 'production') {
      this.sendToLoggingService(errorLog);
    }

    return correlationId;
  }

  /**
   * Log an API error
   */
  logApiError(
    endpoint: string,
    method: string,
    status: number,
    error: Error | string,
    requestData?: any
  ): string {
    return this.logError(error, {
      type: 'api_error',
      endpoint,
      method,
      status,
      requestData,
    });
  }

  /**
   * Log a component error
   */
  logComponentError(
    componentName: string,
    error: Error | string,
    props?: any
  ): string {
    return this.logError(error, {
      type: 'component_error',
      componentName,
      props,
    });
  }

  /**
   * Get recent error logs
   */
  getRecentLogs(count: number = 10): ErrorLog[] {
    return this.logs.slice(-count);
  }

  /**
   * Get error by correlation ID
   */
  getErrorByCorrelationId(correlationId: string): ErrorLog | undefined {
    return this.logs.find(log => log.correlationId === correlationId);
  }

  /**
   * Clear all logs
   */
  clearLogs(): void {
    this.logs = [];
  }

  /**
   * Send error to logging service (placeholder)
   */
  private sendToLoggingService(errorLog: ErrorLog): void {
    // In production, implement actual logging service integration
    // Examples:
    // - Sentry.captureException()
    // - LogRocket.captureException()
    // - fetch('/api/logs', { method: 'POST', body: JSON.stringify(errorLog) })
    
    // For now, just log to console
    console.error('[Production Error]', errorLog);
  }
}

// Export singleton instance
export const errorLogger = new ErrorLogger();

/**
 * User-friendly error messages for common error types
 */
export const getUserFriendlyMessage = (error: Error | string): string => {
  const message = error instanceof Error ? error.message : error;

  // Network errors
  if (message.includes('fetch') || message.includes('network')) {
    return 'Network error. Please check your connection and try again.';
  }

  // Authentication errors
  if (message.includes('401') || message.includes('unauthorized')) {
    return 'Authentication required. Please log in again.';
  }

  // Permission errors
  if (message.includes('403') || message.includes('forbidden')) {
    return 'You don\'t have permission to perform this action.';
  }

  // Not found errors
  if (message.includes('404') || message.includes('not found')) {
    return 'The requested resource was not found.';
  }

  // Server errors
  if (message.includes('500') || message.includes('server error')) {
    return 'Server error. Please try again later.';
  }

  // Timeout errors
  if (message.includes('timeout')) {
    return 'Request timed out. Please try again.';
  }

  // Validation errors
  if (message.includes('validation') || message.includes('invalid')) {
    return 'Invalid data. Please check your input and try again.';
  }

  // Default message
  return 'An unexpected error occurred. Please try again.';
};
