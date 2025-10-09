'use client'

import { useEffect, useState } from 'react'
import { Search, Loader2, AlertCircle, RefreshCw } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { NewSessionButton } from './new-session-button'
import { SessionList } from './session-list'
import { useSessionStore } from '@/lib/store/session-store'
import { useAuthStore } from '@/lib/store/auth-store'
import { cn } from '@/lib/utils'

interface SessionSidebarProps {
  className?: string
}

export function SessionSidebar({ className }: SessionSidebarProps) {
  const [sidebarHeight, setSidebarHeight] = useState(0)
  const { isAuthenticated } = useAuthStore()
  const { 
    sessions,
    isLoading, 
    error, 
    searchTerm,
    setSearchTerm,
    loadSessions,
  } = useSessionStore()

  // Calculate available height for the session list
  useEffect(() => {
    const calculateHeight = () => {
      const header = 64 // Header height
      const searchAndButton = 120 // Search input + new session button + padding
      const footer = 40 // Session count footer + padding
      const available = window.innerHeight - header - searchAndButton - footer - 16 // Extra padding
      setSidebarHeight(Math.max(400, available))
    }

    calculateHeight()
    window.addEventListener('resize', calculateHeight)
    return () => window.removeEventListener('resize', calculateHeight)
  }, [])

  // Não carregar sessions aqui - delegado para chat/page.tsx para evitar duplicação

  // Don't render if not authenticated
  if (!isAuthenticated) {
    return null
  }

  const handleRetry = () => {
    console.log('🔄 Manual refresh triggered - forcing API call')
    loadSessions(true) // Force reload ignoring cache
  }

  return (
    <div className={cn(
      "hidden lg:flex flex-col w-80 h-full bg-background border-r border-border",
      className
    )}>
      {/* Sidebar Header */}
      <div className="shrink-0 p-4 border-b border-border">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-foreground">Sessions</h2>
          <Button
            variant="ghost"
            size="sm"
            onClick={handleRetry}
            disabled={isLoading}
            className="h-8 w-8 p-0"
            title="Refresh sessions"
          >
            {isLoading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <RefreshCw className="h-4 w-4" />
            )}
          </Button>
        </div>

        {/* Search Input */}
        <div className="relative mb-3">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search sessions..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-9"
            disabled={isLoading}
          />
        </div>

        {/* New Session Button */}
        <NewSessionButton className="w-full" />
      </div>

      {/* Sessions Content */}
      <div className="flex-1 flex flex-col min-h-0">
        {error ? (
          // Error State
          <div className="p-4">
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription className="text-sm">
                {error}
              </AlertDescription>
            </Alert>
            <Button
              variant="outline"
              size="sm"
              onClick={handleRetry}
              className="w-full mt-3"
              disabled={isLoading}
            >
              {isLoading ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Retrying...
                </>
              ) : (
                'Try Again'
              )}
            </Button>
          </div>
        ) : isLoading && sessions.length === 0 ? (
          // Initial Loading State
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center space-y-2">
              <Loader2 className="h-8 w-8 animate-spin mx-auto text-muted-foreground" />
              <p className="text-sm text-muted-foreground">Loading sessions...</p>
            </div>
          </div>
        ) : (
          // Sessions List
          <SessionList 
            height={sidebarHeight} 
            className="flex-1"
          />
        )}
      </div>

      {/* Session Count Footer */}
      {sessions.length > 0 && !isLoading && (
        <div className="shrink-0 px-4 py-2 border-t border-border bg-muted/30">
          <p className="text-xs text-muted-foreground text-center">
            {sessions.length} session{sessions.length !== 1 ? 's' : ''}
            {searchTerm && ` • ${searchTerm.length > 0 ? 'filtered' : 'all'}`}
          </p>
        </div>
      )}
    </div>
  )
}