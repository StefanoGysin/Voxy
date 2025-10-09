'use client'

import { useEffect, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import { useChatStore } from '@/lib/store/chat-store'
import { useAuthStore } from '@/lib/store/auth-store'
import { useSessionStore } from '@/lib/store/session-store'
import { useChatFallback } from '@/lib/hooks/use-chat-fallback'
import { MessageList } from './message-list'
import { MessageInput } from './message-input'
import { ConnectionStatusEnhanced } from './connection-status-enhanced'
import { CostTracker } from './cost-tracker'
import { useVisionStore } from '@/lib/store/vision-store'
import { cn } from '@/lib/utils'

interface ChatContainerProps {
  className?: string
}

export function ChatContainer({ className }: ChatContainerProps) {
  const router = useRouter()
  const { user, isAuthenticated, isLoading: authLoading } = useAuthStore()
  const { messages, isTyping, currentSession } = useChatStore()
  const { selectSession } = useSessionStore()
  const { showCostTracker } = useVisionStore()
  const { 
    mode, 
    connectionState, 
    sendMessage, 
    isLoading: chatLoading, 
    lastError,
    canRetryWebSocket,
    retryWebSocket,
    forceRestMode,
    wsRetryCount,
    maxWebSocketRetries
  } = useChatFallback({
    maxWebSocketRetries: 3,
    fallbackToRest: true,
    retryDelay: 5000
  })

  // Auth is initialized in the main page component, not here

  // Redirect if not authenticated
  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/auth/login')
    }
  }, [isAuthenticated, authLoading, router])

  // Restore session and messages after authentication
  useEffect(() => {
    const restoreSession = async () => {
      if (!isAuthenticated) return
      
      console.log('🔄 Starting session restoration after page reload...')
      
      // Get current state from both stores
      const chatState = useChatStore.getState()
      const sessionState = useSessionStore.getState()
      
      // Try to determine which session to restore from multiple sources
      const sessionToRestore = currentSession || sessionState.currentSessionId
      
      console.log('📊 Restoration state:', {
        chatCurrentSession: currentSession,
        sessionCurrentId: sessionState.currentSessionId,
        sessionToRestore,
        messagesCount: chatState.messages.length
      })
      
      if (!sessionToRestore) {
        console.log('⚠️ No session to restore found')
        return
      }
      
      // Check if we already have messages for this session (avoid unnecessary reload)
      const hasMessagesForSession = chatState.messages.some(msg => msg.sessionId === sessionToRestore)
      
      if (hasMessagesForSession && chatState.messages.length > 0) {
        console.log(`✅ Session ${sessionToRestore} already has ${chatState.messages.length} messages, skipping reload`)
        // Ensure both stores are synchronized
        if (currentSession !== sessionToRestore) {
          chatState.setCurrentSession(sessionToRestore)
        }
        return
      }
      
      try {
        console.log(`🔄 Restoring session from server: ${sessionToRestore}`)
        // This will load messages from server and sync with local state
        await selectSession(sessionToRestore)
        console.log('✅ Session restored successfully')
      } catch (error) {
        console.error('❌ Failed to restore session:', error)
        // If session restore fails, clear the invalid session
        useChatStore.getState().setCurrentSession('')
        useSessionStore.getState().clearCurrentSession()
      }
    }

    // Only restore once when component mounts and user is authenticated
    if (isAuthenticated && !authLoading) {
      console.log('🏃 Triggering session restoration...')
      // Use a slight delay to ensure stores are fully initialized
      const timeoutId = setTimeout(restoreSession, 200)
      return () => clearTimeout(timeoutId)
    }
  }, [isAuthenticated, authLoading, currentSession, selectSession])

  const handleSendMessage = useCallback(async (content: string, selectedAgent?: string, imageUrl?: string) => {
    if (!content.trim() && !imageUrl) return

    try {
      console.log('Sending message via fallback system:', { content, selectedAgent, imageUrl, mode, connectionState })
      
      // For vision messages, we need to pass the image URL
      // The backend will handle the Vision Agent routing based on the imageUrl presence
      const messageData = imageUrl ? { content, imageUrl } : content
      
      // Use the smart fallback system - it handles WebSocket/REST automatically
      await sendMessage(messageData, useChatStore.getState().currentSession || undefined)
    } catch (error) {
      console.error('Send message failed:', error)
      // Error handling is managed by the fallback hook
    }
  }, [sendMessage, mode, connectionState])

  // Show loading state while auth is initializing
  if (authLoading) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center space-y-4">
          <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin mx-auto" />
          <p className="text-muted-foreground">Initializing VOXY...</p>
        </div>
      </div>
    )
  }

  // Don't render if not authenticated (will be redirected)
  if (!isAuthenticated || !user) {
    return null
  }

  return (
    <div className={cn('voxy-chat-container h-full bg-background flex flex-col overflow-hidden', className)}>
      {/* Status Bar - Connection and Cost Tracking */}
      {((connectionState !== 'connected' || mode !== 'websocket') || showCostTracker) && (
        <div className="shrink-0 px-4 py-2 bg-muted/30">
          <div className="flex items-center justify-between">
            {/* Connection Status */}
            {(connectionState !== 'connected' || mode !== 'websocket') && (
              <ConnectionStatusEnhanced 
                mode={mode}
                connectionState={connectionState}
                isLoading={chatLoading}
                lastError={lastError}
                canRetryWebSocket={canRetryWebSocket}
                onRetryWebSocket={retryWebSocket}
                onForceRestMode={forceRestMode}
                wsRetryCount={wsRetryCount}
                maxRetries={maxWebSocketRetries}
              />
            )}
            
            {/* Cost Tracker */}
            {showCostTracker && (
              <CostTracker compact className="ml-auto" />
            )}
          </div>
        </div>
      )}
      
      {/* Scrollable Message Area - Takes all available space */}
      <div className="flex-1 min-h-0 overflow-hidden">
        <MessageList 
          messages={messages}
          isTyping={isTyping}
          className="h-full"
        />
      </div>
      
      {/* Fixed Input at Bottom - Always visible */}
      <div className="shrink-0 border-t border-border bg-background" style={{ paddingBottom: '3rem' }}>
        <MessageInput 
          onSendMessage={handleSendMessage}
          disabled={mode === 'disabled' || chatLoading}
          placeholder={
            mode === 'disabled'
              ? 'Please log in to chat with VOXY'
              : mode === 'websocket' && connectionState === 'connected'
              ? 'Type your message to VOXY... (Real-time)'
              : mode === 'rest'
              ? 'Type your message to VOXY... (Standard mode)'
              : connectionState === 'connecting'
              ? 'Connecting to VOXY...'
              : connectionState === 'failed'
              ? 'Connection issues - check status above'
              : 'Reconnecting to VOXY...'
          }
        />
      </div>
    </div>
  )
}