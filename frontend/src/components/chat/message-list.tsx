'use client'

import { MessageBubble } from './message-bubble'
import { TypingIndicator } from './typing-indicator'
import { ScrollArea } from '@/components/ui/scroll-area'
import { cn } from '@/lib/utils'
import type { Message } from '@/types'

interface MessageListProps {
  messages: Message[]
  isTyping: boolean
  className?: string
}

export function MessageList({ messages, isTyping, className }: MessageListProps) {



  if (messages.length === 0 && !isTyping) {
    return (
      <div className={cn('h-full flex flex-col justify-center items-center', className)}>
        {/* Centered welcome content */}
        <div className="text-center space-y-4 sm:space-y-6 px-4 py-4 max-w-2xl">
          <div className="w-16 h-16 sm:w-20 sm:h-20 bg-gradient-to-br from-blue-500 to-blue-600 rounded-full flex items-center justify-center mx-auto shadow-lg">
            <span className="text-3xl sm:text-4xl">🧠</span>
          </div>
          <div className="space-y-2 sm:space-y-3">
            <h3 className="text-xl sm:text-2xl font-semibold text-foreground">Welcome to VOXY</h3>
            <p className="text-sm sm:text-base text-muted-foreground max-w-lg mx-auto leading-relaxed">
              Start a conversation with our AI agents. They can help with translations, 
              corrections, weather information, calculations, and more!
            </p>
          </div>
          <div className="flex flex-wrap justify-center gap-2 sm:gap-3 mt-6">
            {['🌍 Translate', '✏️ Correct', '🌤️ Weather', '🧮 Calculate'].map((suggestion) => (
              <div
                key={suggestion}
                className="px-3 py-2 sm:px-4 sm:py-2.5 bg-muted/60 hover:bg-muted/80 rounded-full text-sm sm:text-base text-muted-foreground transition-colors cursor-pointer"
              >
                {suggestion}
              </div>
            ))}
          </div>
        </div>
      </div>
    )
  }

  return (
    <div 
      className={cn('h-full flex flex-col overflow-hidden', className)}
    >
      {/* Messages Container - Takes all available space and scrolls */}
      <div className="flex-1 min-h-0 overflow-hidden">
        <ScrollArea className="h-full">
          <div className="space-y-3 p-4 pt-2 pb-6">
            {messages.map((message, index) => (
              <MessageBubble 
                key={`${message.id || index}-${message.timestamp}`}
                message={message}
                className="px-0"
              />
            ))}
            {/* Extra space at bottom for better scrolling experience */}
            <div className="h-4" />
          </div>
        </ScrollArea>
      </div>
      
      {/* Typing Indicator - Fixed at bottom when visible */}
      {isTyping && (
        <div className="shrink-0 border-t bg-background/95 backdrop-blur">
          <TypingIndicator className="px-4 py-2" />
        </div>
      )}
    </div>
  )
}