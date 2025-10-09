'use client'

import { useEffect, useState, useCallback } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Separator } from '@/components/ui/separator'
import { cn } from '@/lib/utils'
import { useChatAPI } from '@/lib/hooks/use-chat-api'
import { useChatStore } from '@/lib/store/chat-store'
import { Plus, MessageSquare, Clock, Search } from 'lucide-react'
import { Input } from '@/components/ui/input'

interface ChatSession {
  id: string
  title: string
  created_at: string
  updated_at: string
  user_id: string
}

interface ChatSidebarProps {
  className?: string
  onClose?: () => void
}

export function ChatSidebar({ className, onClose }: ChatSidebarProps) {
  const [sessions, setSessions] = useState<ChatSession[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [searchTerm, setSearchTerm] = useState('')
  
  const { loadChatHistory, createNewSession } = useChatAPI()
  const { currentSession, setCurrentSession } = useChatStore()

  const loadSessions = useCallback(async () => {
    try {
      setIsLoading(true)
      const result = await loadChatHistory()
      if ('sessions' in result && result.sessions) {
        setSessions(result.sessions)
      }
    } catch (error) {
      console.error('Failed to load sessions:', error)
    } finally {
      setIsLoading(false)
    }
  }, [loadChatHistory])

  // Load sessions on mount
  useEffect(() => {
    loadSessions()
  }, [loadSessions])

  const handleCreateNewSession = async () => {
    try {
      await createNewSession('New Chat')
      await loadSessions() // Reload sessions
      onClose?.()
    } catch (error) {
      console.error('Failed to create session:', error)
    }
  }

  const handleSelectSession = async (sessionId: string) => {
    try {
      setIsLoading(true)
      await loadChatHistory(sessionId)
      setCurrentSession(sessionId)
      onClose?.()
    } catch (error) {
      console.error('Failed to load session:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const filteredSessions = sessions.filter(session =>
    session.title.toLowerCase().includes(searchTerm.toLowerCase())
  )

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    const now = new Date()
    const diffTime = Math.abs(now.getTime() - date.getTime())
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))

    if (diffDays === 1) return 'Today'
    if (diffDays === 2) return 'Yesterday'
    if (diffDays <= 7) return `${diffDays} days ago`
    
    return date.toLocaleDateString()
  }

  return (
    <Card className={cn('h-full flex flex-col', className)}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg">Chat History</CardTitle>
          {onClose && (
            <Button variant="ghost" size="sm" onClick={onClose}>
              ×
            </Button>
          )}
        </div>
        
        {/* New Chat Button */}
        <Button
          onClick={handleCreateNewSession}
          className="w-full justify-start gap-2"
          disabled={isLoading}
        >
          <Plus className="h-4 w-4" />
          New Chat
        </Button>

        {/* Search */}
        <div className="relative">
          <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search conversations..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-8"
          />
        </div>
      </CardHeader>

      <Separator />

      <CardContent className="flex-1 p-0">
        <ScrollArea className="h-full">
          {isLoading && sessions.length === 0 ? (
            <div className="p-4 text-center text-muted-foreground">
              <div className="w-6 h-6 border-2 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-2" />
              Loading conversations...
            </div>
          ) : filteredSessions.length === 0 ? (
            <div className="p-4 text-center text-muted-foreground">
              {searchTerm ? (
                <>
                  <Search className="h-8 w-8 mx-auto mb-2 opacity-50" />
                  No conversations found for &ldquo;{searchTerm}&rdquo;
                </>
              ) : (
                <>
                  <MessageSquare className="h-8 w-8 mx-auto mb-2 opacity-50" />
                  No conversations yet. Start a new chat!
                </>
              )}
            </div>
          ) : (
            <div className="p-2 space-y-1">
              {filteredSessions.map((session) => {
                const isActive = currentSession === session.id
                
                return (
                  <Button
                    key={session.id}
                    variant={isActive ? "secondary" : "ghost"}
                    className={cn(
                      'w-full justify-start gap-3 h-auto p-3',
                      'hover:bg-muted transition-colors',
                      isActive && 'bg-secondary'
                    )}
                    onClick={() => handleSelectSession(session.id)}
                    disabled={isLoading}
                  >
                    <MessageSquare className="h-4 w-4 shrink-0" />
                    <div className="flex-1 text-left min-w-0">
                      <div className="font-medium truncate">
                        {session.title}
                      </div>
                      <div className="text-xs text-muted-foreground flex items-center gap-1">
                        <Clock className="h-3 w-3" />
                        {formatDate(session.updated_at)}
                      </div>
                    </div>
                  </Button>
                )
              })}
            </div>
          )}
        </ScrollArea>
      </CardContent>
    </Card>
  )
}