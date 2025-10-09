'use client'

import { useState } from 'react'
import { Plus, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useSessionStore } from '@/lib/store/session-store'

interface NewSessionButtonProps {
  className?: string
}

export function NewSessionButton({ className }: NewSessionButtonProps) {
  const [isCreating, setIsCreating] = useState(false)
  const { createSession, loadSessions } = useSessionStore()

  const handleNewSession = async () => {
    setIsCreating(true)
    try {
      const sessionId = await createSession()
      if (sessionId) {
        console.log('✨ New session created and selected:', sessionId)
        // Force a fresh load of sessions as a safety measure
        setTimeout(() => {
          loadSessions()
        }, 100) // Small delay to ensure backend is consistent
      }
    } catch (error) {
      console.error('Failed to create session:', error)
    } finally {
      setIsCreating(false)
    }
  }

  return (
    <Button
      variant="outline"
      size="sm"
      onClick={handleNewSession}
      disabled={isCreating}
      className={className}
    >
      {isCreating ? (
        <>
          <Loader2 className="h-4 w-4 mr-2 animate-spin" />
          Creating...
        </>
      ) : (
        <>
          <Plus className="h-4 w-4 mr-2" />
          New Chat
        </>
      )}
    </Button>
  )
}