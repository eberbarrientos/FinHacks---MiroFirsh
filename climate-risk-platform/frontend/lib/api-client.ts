/**
 * API client for Climate Risk Platform backend
 */

import { errorLogger } from './error-logger'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public details?: any,
    public correlationId?: string
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

async function handleResponse<T>(response: Response, endpoint: string, method: string): Promise<T> {
  if (!response.ok) {
    const error = await response.json().catch(() => ({ message: 'Unknown error' }))
    const errorMessage = error.message || `HTTP ${response.status}`
    
    // Log error with correlation ID
    const correlationId = errorLogger.logApiError(
      endpoint,
      method,
      response.status,
      errorMessage,
      error.details
    )
    
    throw new ApiError(
      errorMessage,
      response.status,
      error.details,
      correlationId
    )
  }
  return response.json()
}

export const apiClient = {
  async get<T>(path: string): Promise<T> {
    const response = await fetch(`${API_BASE_URL}${path}`)
    return handleResponse<T>(response, path, 'GET')
  },

  async post<T>(path: string, data?: any): Promise<T> {
    const response = await fetch(`${API_BASE_URL}${path}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: data ? JSON.stringify(data) : undefined,
    })
    return handleResponse<T>(response, path, 'POST')
  },

  async put<T>(path: string, data: any): Promise<T> {
    const response = await fetch(`${API_BASE_URL}${path}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    })
    return handleResponse<T>(response, path, 'PUT')
  },

  async delete<T>(path: string): Promise<T> {
    const response = await fetch(`${API_BASE_URL}${path}`, {
      method: 'DELETE',
    })
    return handleResponse<T>(response, path, 'DELETE')
  },

  async uploadFile<T>(path: string, file: File): Promise<T> {
    const formData = new FormData()
    formData.append('file', file)

    const response = await fetch(`${API_BASE_URL}${path}`, {
      method: 'POST',
      body: formData,
    })
    return handleResponse<T>(response, path, 'POST')
  },
}
