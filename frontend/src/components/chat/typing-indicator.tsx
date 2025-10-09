'use client'

import { cn } from '@/lib/utils'

interface TypingIndicatorProps {
  className?: string
  agent?: string
}

export function TypingIndicator({ className, agent = 'VOXY' }: TypingIndicatorProps) {
  return (
    <div className={cn('flex items-center gap-3 p-4', className)}>
      <div className="w-8 h-8 bg-muted rounded-full flex items-center justify-center">
        <span className="text-sm">🧠</span>
      </div>
      
      <div className="flex flex-col gap-1">
        <div className="text-sm font-medium text-muted-foreground">
          {agent} is typing
        </div>
        <div className="voxy-typing-indicator">
          <div className="voxy-typing-dot"></div>
          <div className="voxy-typing-dot"></div>
          <div className="voxy-typing-dot"></div>
        </div>
      </div>
    </div>
  )
}