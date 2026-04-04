/**
 * Error Boundary Component
 * 
 * Catches React errors and displays fallback UI
 * Implements graceful error handling for dashboard components
 */

'use client'

import React, { Component, ReactNode } from 'react'
import { errorLogger, getUserFriendlyMessage } from '@/lib/error-logger'

interface Props {
  children: ReactNode
  fallback?: ReactNode
  componentName?: string
}

interface State {
  hasError: boolean
  error: Error | null
  correlationId: string | null
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { hasError: false, error: null, correlationId: null }
  }

  static getDerivedStateFromError(error: Error): Partial<State> {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    // Log error with correlation ID
    const correlationId = errorLogger.logComponentError(
      this.props.componentName || 'Unknown Component',
      error,
      errorInfo
    )
    
    this.setState({ correlationId })
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback
      }

      return (
        <div className="bg-red-500/10 border border-red-500/20 rounded-2xl p-6">
          <div className="flex items-start space-x-3">
            <svg
              className="w-6 h-6 text-red-400 flex-shrink-0 mt-0.5"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
              />
            </svg>
            <div className="flex-1">
              <h3 className="text-lg font-semibold text-red-400 mb-1">
                Something went wrong
              </h3>
              <p className="text-sm text-slate-400 mb-3">
                {this.state.error ? getUserFriendlyMessage(this.state.error) : 'This component encountered an error and couldn\'t be displayed.'}
              </p>
              {this.state.correlationId && (
                <p className="text-xs text-slate-500 mb-3">
                  Error ID: <code className="bg-slate-900/50 px-2 py-0.5 rounded">{this.state.correlationId}</code>
                </p>
              )}
              {this.state.error && (
                <details className="text-xs text-slate-500">
                  <summary className="cursor-pointer hover:text-slate-400">
                    Technical details
                  </summary>
                  <pre className="mt-2 p-3 bg-slate-900/50 rounded-lg overflow-auto max-h-40">
                    {this.state.error.toString()}
                    {this.state.error.stack && `\n\n${this.state.error.stack}`}
                  </pre>
                </details>
              )}
              <button
                onClick={() => this.setState({ hasError: false, error: null, correlationId: null })}
                className="mt-3 px-4 py-2 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400 hover:bg-red-500/20 transition-colors text-sm"
              >
                Try again
              </button>
            </div>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}
