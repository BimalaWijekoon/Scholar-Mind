import { create } from 'zustand'
import type { Message } from '@/types'
import { queryService } from '@/services/api'

interface ChatState {
  messages: Message[]
  isLoading: boolean
  sessionId: string
  sendMessage: (content: string) => Promise<void>
  clearMessages: () => void
  setSessionId: (id: string) => void
}

function generateSessionId(): string {
  return Math.random().toString(36).substring(2, 15)
}

export const useChatStore = create<ChatState>((set, get) => ({
  messages: [],
  isLoading: false,
  sessionId: generateSessionId(),

  sendMessage: async (content: string) => {
    const { sessionId, messages } = get()

    // Add user message
    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content,
      timestamp: new Date().toISOString(),
    }

    set({ messages: [...messages, userMessage], isLoading: true })

    try {
      // Send to API
      const response = await queryService.ask(content, sessionId)

      // Add assistant message
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.answer,
        sources: response.sources,
        timestamp: new Date().toISOString(),
      }

      set((state) => ({
        messages: [...state.messages, assistantMessage],
        isLoading: false,
      }))
    } catch (error) {
      // Add error message
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: 'Sorry, I encountered an error processing your request.',
        timestamp: new Date().toISOString(),
      }

      set((state) => ({
        messages: [...state.messages, errorMessage],
        isLoading: false,
      }))
    }
  },

  clearMessages: () => set({ messages: [], sessionId: generateSessionId() }),

  setSessionId: (sessionId) => set({ sessionId }),
}))
