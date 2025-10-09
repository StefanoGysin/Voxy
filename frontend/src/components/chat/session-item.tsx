'use client'

import { useState } from 'react'
import { formatDistanceToNow } from 'date-fns'
import { MessageSquare, MoreHorizontal, Edit2, Trash2, Check, X } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { cn } from '@/lib/utils'
import { useSessionStore, type SessionSummary } from '@/lib/store/session-store'

interface SessionItemProps {
  session: SessionSummary
  isActive: boolean
  onClick: () => void
}

export function SessionItem({ session, isActive, onClick }: SessionItemProps) {
  const [isEditing, setIsEditing] = useState(false)
  const [editTitle, setEditTitle] = useState(session.title || '')
  const { updateSessionTitle, deleteSession } = useSessionStore()

  const handleEdit = async () => {
    if (!editTitle.trim()) {
      setIsEditing(false)
      setEditTitle(session.title || '')
      return
    }

    await updateSessionTitle(session.id, editTitle.trim())
    setIsEditing(false)
  }

  const handleCancel = () => {
    setIsEditing(false)
    setEditTitle(session.title || '')
  }

  const handleDelete = async () => {
    if (confirm('Are you sure you want to delete this session? This action cannot be undone.')) {
      await deleteSession(session.id)
    }
  }

  const displayTitle = session.title || 'New Chat'

  return (
    <div
      className={cn(
        'group relative flex flex-col gap-1 p-2 rounded-lg transition-all duration-200 cursor-pointer border border-transparent',
        'hover:bg-muted/50 hover:border-border/50',
        isActive && 'bg-muted border-border shadow-sm'
      )}
      onClick={onClick}
    >
      {/* Header with title and menu */}
      <div className="flex items-start justify-between gap-2 min-h-[20px]">
        <div className="flex items-center gap-2 flex-1 min-w-0">
          <MessageSquare className="h-4 w-4 text-muted-foreground/70 shrink-0 mt-0.5" />
          
          {isEditing ? (
            <div className="flex items-center gap-1 flex-1" onClick={(e) => e.stopPropagation()}>
              <Input
                value={editTitle}
                onChange={(e) => setEditTitle(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') handleEdit()
                  if (e.key === 'Escape') handleCancel()
                }}
                className="h-6 text-sm px-2 py-0"
                autoFocus
                onBlur={handleEdit}
              />
              <Button
                size="sm"
                variant="ghost"
                className="h-6 w-6 p-0"
                onClick={handleEdit}
              >
                <Check className="h-3 w-3" />
              </Button>
              <Button
                size="sm"
                variant="ghost"
                className="h-6 w-6 p-0"
                onClick={handleCancel}
              >
                <X className="h-3 w-3" />
              </Button>
            </div>
          ) : (
            <h4 className="text-sm font-medium text-foreground truncate flex-1 leading-5">
              {displayTitle}
            </h4>
          )}
        </div>

        {!isEditing && (
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                variant="ghost"
                size="sm"
                className="h-6 w-6 p-0 opacity-0 group-hover:opacity-100 transition-opacity"
                onClick={(e) => e.stopPropagation()}
              >
                <MoreHorizontal className="h-3 w-3" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem onClick={(e) => {
                e.stopPropagation()
                setIsEditing(true)
              }}>
                <Edit2 className="h-4 w-4 mr-2" />
                Rename
              </DropdownMenuItem>
              <DropdownMenuItem 
                onClick={(e) => {
                  e.stopPropagation()
                  handleDelete()
                }}
                className="text-destructive focus:text-destructive"
              >
                <Trash2 className="h-4 w-4 mr-2" />
                Delete
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        )}
      </div>

      {/* Meta info only */}
      <div className="flex items-center justify-between text-xs text-muted-foreground/60 pl-6">
        <span>{session.message_count} message{session.message_count !== 1 ? 's' : ''}</span>
        <span>
          {formatDistanceToNow(new Date(session.updated_at), { addSuffix: true })}
        </span>
      </div>

      {/* Active indicator */}
      {isActive && (
        <div className="absolute left-0 top-3 bottom-3 w-1 bg-primary rounded-r-full" />
      )}
    </div>
  )
}