'use client'

import { useState, useEffect } from 'react'
import { Menu, X, Search } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { ScrollArea } from '@/components/ui/scroll-area'
import { NewSessionButton } from './new-session-button'
import { SessionItem } from './session-item'
import { useSessionStore } from '@/lib/store/session-store'
import { cn } from '@/lib/utils'

interface SessionMobileToggleProps {
  className?: string
}

export function SessionMobileToggle({ className }: SessionMobileToggleProps) {
  const [isOpen, setIsOpen] = useState(false)
  const { 
    sessions,
    currentSessionId,
    selectSession,
    searchTerm,
    setSearchTerm,
    getGroupedSessions,
    getFilteredSessions,
    loadSessions,
  } = useSessionStore()

  // Load sessions when modal opens
  useEffect(() => {
    if (isOpen && sessions.length === 0) {
      loadSessions()
    }
  }, [isOpen, sessions.length, loadSessions])

  const handleSessionSelect = async (sessionId: string) => {
    await selectSession(sessionId)
    setIsOpen(false)
  }

  const sessionsToShow = searchTerm ? getFilteredSessions() : sessions
  const groupedSessions = searchTerm ? [] : getGroupedSessions()

  return (
    <>
      {/* Toggle Button - Only visible on mobile */}
      <Button
        variant="ghost"
        size="sm"
        onClick={() => setIsOpen(true)}
        className={cn("lg:hidden", className)}
      >
        <Menu className="h-5 w-5" />
      </Button>

      {/* Mobile Sessions Dialog */}
      <Dialog open={isOpen} onOpenChange={setIsOpen}>
        <DialogContent className="h-[90vh] max-w-sm p-0 gap-0">
          <DialogHeader className="px-4 py-3 border-b">
            <div className="flex items-center justify-between">
              <DialogTitle className="text-lg">Chat Sessions</DialogTitle>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setIsOpen(false)}
                className="h-8 w-8 p-0"
              >
                <X className="h-4 w-4" />
              </Button>
            </div>
          </DialogHeader>

          <div className="flex-1 flex flex-col min-h-0">
            {/* Search and New Session */}
            <div className="p-4 space-y-3 border-b">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search sessions..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-9"
                />
              </div>
              <NewSessionButton className="w-full" />
            </div>

            {/* Sessions List */}
            <ScrollArea className="flex-1">
              <div className="p-2 space-y-1">
                {sessionsToShow.length === 0 ? (
                  <div className="text-center py-8 text-muted-foreground">
                    <p className="text-sm">
                      {searchTerm ? 'No sessions match your search' : 'No chat sessions yet'}
                    </p>
                    {!searchTerm && (
                      <p className="text-xs mt-1">Start a new conversation to get started</p>
                    )}
                  </div>
                ) : searchTerm ? (
                  // Flat list when searching
                  sessionsToShow.map(session => (
                    <SessionItem
                      key={session.id}
                      session={session}
                      isActive={session.id === currentSessionId}
                      onClick={() => handleSessionSelect(session.id)}
                    />
                  ))
                ) : (
                  // Grouped list when not searching
                  groupedSessions.map(group => (
                    <div key={group.label} className="mb-4">
                      <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider px-3 py-2">
                        {group.label}
                      </h3>
                      <div className="space-y-1">
                        {group.sessions.map(session => (
                          <SessionItem
                            key={session.id}
                            session={session}
                            isActive={session.id === currentSessionId}
                            onClick={() => handleSessionSelect(session.id)}
                          />
                        ))}
                      </div>
                    </div>
                  ))
                )}
              </div>
            </ScrollArea>
          </div>
        </DialogContent>
      </Dialog>
    </>
  )
}