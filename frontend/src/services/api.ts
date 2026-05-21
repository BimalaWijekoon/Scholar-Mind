/// <reference types="vite/client" />
import axios, { AxiosInstance, AxiosProgressEvent } from 'axios'
import type { Document, GraphData, SearchResult } from '@/types'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'

// Create axios instance
const api: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor
api.interceptors.request.use(
  (config) => {
    // Add auth token if available
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// Response interceptor
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Handle unauthorized
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// Document API
export const documentService = {
  async list(): Promise<Document[]> {
    const { data } = await api.get('/documents')
    return data
  },

  async get(id: string): Promise<Document> {
    const { data } = await api.get(`/documents/${id}`)
    return data
  },

  async upload(
    file: File,
    onProgress?: (progress: number) => void
  ): Promise<Document> {
    const formData = new FormData()
    formData.append('file', file)

    const { data } = await api.post('/documents/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent: AxiosProgressEvent) => {
        if (onProgress && progressEvent.total) {
          const progress = Math.round(
            (progressEvent.loaded * 100) / progressEvent.total
          )
          onProgress(progress)
        }
      },
    })

    return data
  },

  async delete(id: string): Promise<void> {
    await api.delete(`/documents/${id}`)
  },

  async reprocess(id: string): Promise<void> {
    await api.post(`/documents/${id}/reprocess`)
  },
}

// Query API
export const queryService = {
  async ask(question: string, sessionId?: string): Promise<{
    answer: string
    sources: Array<{ id: string; title: string; text: string }>
    confidence: number
  }> {
    const { data } = await api.post('/query/ask', {
      question,
      session_id: sessionId,
    })
    return data
  },

  async chat(message: string, sessionId: string): Promise<{
    response: string
    sources: Array<{ id: string; title: string; text: string }>
  }> {
    const { data } = await api.post('/query/chat', {
      message,
      session_id: sessionId,
    })
    return data
  },
}

// Graph API
export const graphService = {
  async getData(centerEntity?: string, depth?: number): Promise<GraphData> {
    const params = new URLSearchParams()
    if (centerEntity) params.append('center', centerEntity)
    if (depth) params.append('depth', depth.toString())

    const { data } = await api.get(`/graph?${params}`)
    return data
  },

  async getEntity(id: string): Promise<{
    id: string
    label: string
    type: string
    properties: Record<string, any>
    neighbors: Array<{ id: string; label: string; type: string }>
  }> {
    const { data } = await api.get(`/graph/entities/${id}`)
    return data
  },

  async findPath(source: string, target: string): Promise<{
    path: Array<{ id: string; label: string }>
    length: number
  }> {
    const { data } = await api.get('/graph/path', {
      params: { source, target },
    })
    return data
  },

  async getCommunities(): Promise<Array<{
    id: string
    label: string
    size: number
    nodes: string[]
  }>> {
    const { data } = await api.get('/graph/communities')
    return data
  },
}

// Search API
export const searchService = {
  async search(
    query: string,
    options?: {
      filters?: Record<string, any>
      limit?: number
    }
  ): Promise<{
    results: SearchResult[]
    total: number
  }> {
    const { data } = await api.post('/search', {
      query,
      ...options,
    })
    return data
  },
}

// Report API
export const reportService = {
  async generate(topic: string, documentIds?: string[]): Promise<{
    id: string
    status: string
  }> {
    const { data } = await api.post('/reports/generate', {
      topic,
      document_ids: documentIds,
    })
    return data
  },

  async get(id: string): Promise<{
    id: string
    topic: string
    content: string
    sources: string[]
    createdAt: string
  }> {
    const { data } = await api.get(`/reports/${id}`)
    return data
  },
}

export default api
