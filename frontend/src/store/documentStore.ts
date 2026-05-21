import { create } from 'zustand'
import type { Document } from '@/types'

interface DocumentState {
  documents: Document[]
  isLoading: boolean
  error: string | null
  addDocument: (doc: Document) => void
  removeDocument: (id: string) => void
  updateDocument: (id: string, updates: Partial<Document>) => void
  setDocuments: (docs: Document[]) => void
  setLoading: (loading: boolean) => void
  setError: (error: string | null) => void
}

export const useDocumentStore = create<DocumentState>((set) => ({
  documents: [],
  isLoading: false,
  error: null,

  addDocument: (doc) =>
    set((state) => ({
      documents: [doc, ...state.documents],
    })),

  removeDocument: (id) =>
    set((state) => ({
      documents: state.documents.filter((d) => d.id !== id),
    })),

  updateDocument: (id, updates) =>
    set((state) => ({
      documents: state.documents.map((d) =>
        d.id === id ? { ...d, ...updates } : d
      ),
    })),

  setDocuments: (documents) => set({ documents }),

  setLoading: (isLoading) => set({ isLoading }),

  setError: (error) => set({ error }),
}))
