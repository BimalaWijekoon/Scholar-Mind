import { create } from 'zustand'
import { graphService } from '@/services/api'

interface GraphNode {
  id: string
  label: string
  type: string
  size?: number
  x?: number
  y?: number
}

interface GraphEdge {
  source: string
  target: string
  type: string
}

interface GraphState {
  nodes: GraphNode[]
  edges: GraphEdge[]
  selectedNode: GraphNode | null
  isLoading: boolean
  error: string | null
  fetchGraph: (centerEntity?: string, depth?: number) => Promise<void>
  setSelectedNode: (node: GraphNode | null) => void
  setNodes: (nodes: GraphNode[]) => void
  setEdges: (edges: GraphEdge[]) => void
}

export const useGraphStore = create<GraphState>((set) => ({
  nodes: [],
  edges: [],
  selectedNode: null,
  isLoading: false,
  error: null,

  fetchGraph: async (centerEntity, depth) => {
    set({ isLoading: true, error: null })

    try {
      const data = await graphService.getData(centerEntity, depth)
      set({
        nodes: data.nodes,
        edges: data.edges,
        isLoading: false,
      })
    } catch (error) {
      set({
        error: 'Failed to fetch graph data',
        isLoading: false,
      })
    }
  },

  setSelectedNode: (selectedNode) => set({ selectedNode }),

  setNodes: (nodes) => set({ nodes }),

  setEdges: (edges) => set({ edges }),
}))
