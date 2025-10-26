// Core types for VOXY frontend

export type Agent = 
  | 'user' 
  | 'voxy' 
  | 'translator' 
  | 'corrector' 
  | 'weather' 
  | 'calculator'
  | 'vision'
  | 'system'

export type MessageStatus = 
  | 'pending' 
  | 'sending' 
  | 'sent' 
  | 'delivered' 
  | 'error'

export type ConnectionState = 
  | 'disconnected' 
  | 'connecting' 
  | 'connected' 
  | 'reconnecting' 
  | 'failed'

export interface Message {
  id: string
  content: string
  agent: Agent
  timestamp: Date
  status: MessageStatus
  sessionId: string
  imageUrl?: string
  visionMetadata?: {
    modelUsed?: string  // Flexible - accepts any model configured via backend
    analysisType?: 'simple' | 'detailed' | 'chain-of-thought'
    confidence?: number
    cost?: number
    processingTime?: number
  }
  metadata?: {
    processingTime?: number
    cached?: boolean
    requestId?: string
  }
}

export interface PendingMessage {
  id: string
  content: string
  timestamp: Date
  retryCount: number
}

export interface ChatSession {
  id: string
  title: string
  createdAt: Date
  updatedAt: Date
  userId: string
  messageCount: number
}

export interface User {
  id: string
  email?: string
  full_name?: string
  avatar_url?: string
}

// Vision Agent specific types
export interface ImageUpload {
  id: string
  file: File
  preview: string
  status: 'uploading' | 'uploaded' | 'error'
  progress?: number
  uploadedUrl?: string
}

export interface VisionAnalysis {
  id: string
  imageUrl: string
  analysis: string
  modelUsed: string  // Flexible - accepts any model configured via backend
  analysisType: 'simple' | 'detailed' | 'chain-of-thought'
  confidence?: number
  cost: number
  processingTime: number
  timestamp: Date
}

export interface CostMetrics {
  totalCost: number
  monthlyBudget: number
  dailyUsage: number
  gpt5Usage: number
  fallbackUsage: number  // Generic fallback model usage (was gpt4oFallbackUsage)
  lastReset: Date
}

// Agent configuration for UI
export interface AgentConfig {
  color: string
  icon: string
  name: string
  gradient: string
  description?: string
}

export const agentConfigs: Record<Agent, AgentConfig> = {
  user: {
    color: 'gray',
    icon: '👤',
    name: 'You',
    gradient: 'from-gray-500 to-gray-600'
  },
  voxy: {
    color: 'blue',
    icon: '🧠',
    name: 'VOXY',
    gradient: 'from-blue-500 to-blue-600',
    description: 'AI Orchestrator'
  },
  translator: {
    color: 'emerald',
    icon: '🌍',
    name: 'Translator',
    gradient: 'from-emerald-500 to-emerald-600',
    description: 'Language Translation'
  },
  corrector: {
    color: 'violet',
    icon: '✏️',
    name: 'Corrector',
    gradient: 'from-violet-500 to-violet-600',
    description: 'Text Correction'
  },
  weather: {
    color: 'cyan',
    icon: '🌤️',
    name: 'Weather',
    gradient: 'from-cyan-500 to-cyan-600',
    description: 'Weather Information'
  },
  calculator: {
    color: 'amber',
    icon: '🧮',
    name: 'Calculator',
    gradient: 'from-amber-500 to-amber-600',
    description: 'Mathematical Calculations'
  },
  vision: {
    color: 'purple',
    icon: '👁️',
    name: 'Vision Agent',
    gradient: 'from-purple-500 to-purple-600',
    description: 'Image Analysis & GPT-5 Vision'
  },
  system: {
    color: 'slate',
    icon: '⚙️',
    name: 'System',
    gradient: 'from-slate-500 to-slate-600',
    description: 'System Messages'
  }
}