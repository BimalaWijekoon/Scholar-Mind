// Document types
export interface Document {
  id: string
  title: string
  filename: string
  fileType: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  createdAt: string
  metadata?: {
    authors?: string[]
    abstract?: string
    [key: string]: any
  }
}

// Chat types
export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  sources?: Array<{
    id: string
    title?: string
    text: string
  }>
  timestamp: string
}

// Graph types
export interface GraphNode {
  id: string
  label: string
  type: string
  size?: number
  properties?: Record<string, any>
}

export interface GraphEdge {
  source: string
  target: string
  type: string
  properties?: Record<string, any>
}

export interface GraphData {
  nodes: GraphNode[]
  edges: GraphEdge[]
  statistics?: {
    nodeCount: number
    edgeCount: number
    density: number
  }
}

// Search types
export interface SearchResult {
  id: string
  title: string
  snippet: string
  score: number
  type: 'document' | 'entity'
  documentId?: string
  metadata?: Record<string, any>
}

// Entity types
export interface Entity {
  id: string
  text: string
  type: string
  confidence: number
  documentId: string
  startChar?: number
  endChar?: number
}

// Relation types
export interface Relation {
  id: string
  sourceId: string
  targetId: string
  type: string
  confidence: number
  documentId: string
}

// API Response types
export interface ApiResponse<T> {
  data: T
  status: 'success' | 'error'
  message?: string
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  pageSize: number
  hasMore: boolean
}
