'use client'

import { useMemo } from 'react'
import { FixedSizeList as List } from 'react-window'
import { SessionItem } from './session-item'
import { useSessionStore, type SessionSummary } from '@/lib/store/session-store'
import { cn } from '@/lib/utils'

interface SessionListProps {
  height: number
  className?: string
}

// Unified item type for both flat sessions and grouped items
type ListItem = SessionSummary | { type: 'header'; label: string }

// Unified component for rendering items
const ItemRenderer = ({ index, style, data }: { 
  index: number
  style: React.CSSProperties
  data: { items: ListItem[]; currentSessionId: string | null; selectSession: (sessionId: string) => Promise<void> }
}) => {
  const { items, currentSessionId, selectSession } = data
  const item = items[index]
  
  if (!item) return null

  // Create proper spacing with margin bottom
  const itemStyle = {
    ...style,
    height: (style.height as number) - 4, // Reduce height to create gap
    paddingLeft: '8px',
    paddingRight: '8px',
  }

  // Header item
  if ('type' in item && item.type === 'header') {
    return (
      <div style={itemStyle}>
        <div className="py-3 px-4">
          <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
            {item.label}
          </h3>
        </div>
      </div>
    )
  }

  // Session item
  const session = item as SessionSummary
  return (
    <div style={itemStyle}>
      <div className="pb-1"> {/* Bottom spacing */}
        <SessionItem
          session={session}
          isActive={session.id === currentSessionId}
          onClick={() => selectSession(session.id)}
        />
      </div>
    </div>
  )
}

export function SessionList({ height, className }: SessionListProps) {
  const { 
    getGroupedSessions, 
    getFilteredSessions,
    currentSessionId, 
    selectSession,
    searchTerm 
  } = useSessionStore()

  // Prepare data for virtualized rendering
  const items = useMemo(() => {
    if (searchTerm) {
      // When searching, show flat list without groups
      return getFilteredSessions() as ListItem[]
    } else {
      // Show grouped sessions
      const groups = getGroupedSessions()
      const flatItems: ListItem[] = []
      
      groups.forEach(group => {
        // Add group header
        flatItems.push({
          type: 'header',
          label: group.label,
        })
        
        // Add group sessions
        flatItems.push(...group.sessions)
      })
      
      return flatItems
    }
  }, [searchTerm, getGroupedSessions, getFilteredSessions])

  const itemHeight = 56 // Compact height to fit more sessions on screen

  if (items.length === 0) {
    return (
      <div className={cn("flex items-center justify-center", className)} style={{ height }}>
        <div className="text-center text-muted-foreground">
          <p className="text-sm">
            {searchTerm ? 'No sessions match your search' : 'No chat sessions yet'}
          </p>
          {!searchTerm && (
            <p className="text-xs mt-1">Start a new conversation to get started</p>
          )}
        </div>
      </div>
    )
  }

  const itemData = { items, currentSessionId, selectSession }

  return (
    <div className={className}>
      <List
        height={height}
        width="100%"
        itemCount={items.length}
        itemSize={itemHeight}
        itemData={itemData}
        className="scrollbar-thin scrollbar-thumb-muted-foreground/20 scrollbar-track-transparent"
        style={{
          overflowX: 'hidden',
        }}
      >
        {ItemRenderer}
      </List>
    </div>
  )
}