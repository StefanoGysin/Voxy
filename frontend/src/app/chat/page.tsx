'use client'

import { useEffect } from 'react'
import { useAuthStore } from '@/lib/store/auth-store'
import { useSessionStore } from '@/lib/store/session-store'
import { AuthService } from '@/lib/auth/auth-service'
import { ChatContainer } from '@/components/chat/chat-container'
import { SessionSidebar } from '@/components/chat/session-sidebar'
import { SessionMobileToggle } from '@/components/chat/session-mobile-toggle'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { ArrowLeft } from 'lucide-react'
import Link from 'next/link'

// Chat interface component for authenticated users
function AuthenticatedChat() {
  const { loadSessions } = useSessionStore()
  
  // Load sessions when authenticated chat mounts (debounced)
  useEffect(() => {
    console.log('🔄 AuthenticatedChat mounted, loading sessions...')
    const timer = setTimeout(() => {
      loadSessions() // Usa cache interno do store
    }, 100) // Debounce de 100ms
    
    return () => clearTimeout(timer)
  }, [loadSessions])
  
  return (
    <div className="h-screen bg-background flex flex-col">
      {/* Fixed Header - Always visible at top */}
      <div className="shrink-0 border-b border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-4">
              <Link href="/">
                <Button variant="ghost" size="sm">
                  <ArrowLeft className="h-4 w-4 mr-2" />
                  Web OS
                </Button>
              </Link>
              <div className="h-6 border-l border-border" />
              <div>
                <h1 className="text-lg font-semibold text-foreground">
                  VOXY Chat
                </h1>
                <p className="text-sm text-muted-foreground hidden sm:block">
                  Multi-Agent AI Assistant
                </p>
              </div>
            </div>
            
            <div className="flex items-center space-x-2">
              {/* Mobile Session Toggle */}
              <SessionMobileToggle />
              
              <div className="flex items-center space-x-2 text-sm text-muted-foreground">
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                <span className="hidden sm:inline">Connected</span>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      {/* Main Content with Sidebar */}
      <div className="flex-1 min-h-0 overflow-hidden flex">
        {/* Session Sidebar - Desktop only */}
        <SessionSidebar />
        
        {/* Chat Container - Flex grow to take remaining space */}
        <div className="flex-1 min-h-0 overflow-hidden">
          <ChatContainer className="h-full" />
        </div>
      </div>
    </div>
  )
}

// Landing page for unauthenticated users accessing /chat directly
function UnauthenticatedChatPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-muted/50 flex items-center justify-center p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <div className="w-16 h-16 bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl flex items-center justify-center shadow-lg mx-auto mb-4">
            <span className="text-2xl font-bold text-white">V</span>
          </div>
          <CardTitle className="text-2xl">Sign in to Chat</CardTitle>
          <CardDescription>
            You need to be signed in to access VOXY chat functionality.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-3">
            <Link href="/auth/login" className="block">
              <Button className="w-full" size="lg">
                Sign In
              </Button>
            </Link>
            <Link href="/auth/signup" className="block">
              <Button variant="outline" className="w-full" size="lg">
                Create Account
              </Button>
            </Link>
          </div>
          
          <div className="pt-4 border-t border-border">
            <Link href="/" className="block">
              <Button variant="ghost" className="w-full">
                <ArrowLeft className="h-4 w-4 mr-2" />
                Back to Home
              </Button>
            </Link>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export default function ChatPage() {
  const { isAuthenticated, isLoading } = useAuthStore()

  useEffect(() => {
    // Initialize auth on mount
    AuthService.initializeAuth()
    
    // Setup auth monitoring with proper cleanup
    const cleanup = AuthService.setupAuthMonitoring()
    
    // Cleanup function to stop monitoring when component unmounts
    return () => {
      cleanup()
      AuthService.stopAuthMonitoring()
    }
  }, [])

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center space-y-4">
          <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin mx-auto" />
          <p className="text-muted-foreground">Loading VOXY Chat...</p>
        </div>
      </div>
    )
  }

  // Show chat interface for authenticated users, login prompt for others
  return isAuthenticated ? <AuthenticatedChat /> : <UnauthenticatedChatPage />
}