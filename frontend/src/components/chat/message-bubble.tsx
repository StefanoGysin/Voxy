'use client'

import { cn } from '@/lib/utils'
import { AgentIndicator } from './agent-indicator'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Eye, DollarSign, Clock, Zap, ChevronDown, ChevronUp } from 'lucide-react'
import { useState } from 'react'
import Image from 'next/image'
// import { formatDistanceToNow } from 'date-fns'
import { agentConfigs, type Message } from '@/types'

interface MessageBubbleProps {
  message: Message
  className?: string
}

export function MessageBubble({ message, className }: MessageBubbleProps) {
  const config = agentConfigs[message.agent] || agentConfigs.system
  const isUser = message.agent === 'user'
  const isVisionAgent = message.agent === 'vision'
  const hasImage = Boolean(message.imageUrl)
  const hasVisionMetadata = Boolean(message.visionMetadata)
  
  const [showVisionDetails, setShowVisionDetails] = useState(false)
  
  return (
    <div className={cn(
      'flex gap-3 p-4 voxy-fade-in',
      isUser ? 'justify-end' : 'justify-start',
      className
    )}>
      {!isUser && (
        <Avatar className="w-8 h-8 flex-shrink-0">
          <AvatarFallback 
            className={cn(
              'text-white text-sm font-medium',
              config?.color ? `bg-${config.color}-500 dark:bg-${config.color}-600` : 'bg-slate-500'
            )}
          >
            {config?.icon || '⚙️'}
          </AvatarFallback>
        </Avatar>
      )}
      
      <div className={cn(
        'flex flex-col gap-1 max-w-[70%]',
        isUser ? 'items-end' : 'items-start'
      )}>
        {!isUser && (
          <div className="flex items-center gap-2 mb-1">
            <span className="text-sm font-medium text-foreground">
              {config?.name || 'Unknown'}
            </span>
            <AgentIndicator agent={message.agent} />
          </div>
        )}
        
        <div className="space-y-3">
          {/* Image Display - Only for user messages with images */}
          {hasImage && isUser && (
            <div className="relative max-w-sm sm:max-w-md rounded-lg overflow-hidden border h-64 sm:h-80">
              <Image 
                src={message.imageUrl!} 
                alt="Uploaded image" 
                fill
                className="object-cover"
              />
              <div className="absolute top-2 right-2">
                <Badge variant="secondary" className="text-xs">
                  <Eye className="w-3 h-3 mr-1" />
                  For Analysis
                </Badge>
              </div>
            </div>
          )}
          
          {/* Main Message Content */}
          <div className={cn(
            'px-4 py-3 rounded-2xl shadow-sm',
            'voxy-chat-text leading-relaxed',
            isUser 
              ? 'voxy-chat-bubble-user bg-primary text-primary-foreground' 
              : 'voxy-chat-bubble-agent bg-muted text-foreground border border-border/50'
          )}>
            <p className="whitespace-pre-wrap break-words">{message.content || ''}</p>
          </div>
          
          {/* Vision Analysis Results - Only for Vision Agent responses */}
          {isVisionAgent && hasImage && (
            <div className="max-w-sm sm:max-w-md rounded-lg overflow-hidden border bg-background">
              <div className="relative h-24 sm:h-32">
                <Image 
                  src={message.imageUrl!} 
                  alt="Analyzed image" 
                  fill
                  className="object-cover"
              />
              </div>
              
              {/* Vision Metadata Quick Summary */}
              {hasVisionMetadata && (
                <div className="p-3 space-y-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Badge variant="outline" className="text-xs">
                        <Zap className="w-3 h-3 mr-1" />
                        {message.visionMetadata?.modelUsed?.toUpperCase()}
                      </Badge>
                      {message.visionMetadata?.confidence && (
                        <span className="text-xs text-muted-foreground">
                          {Math.round(message.visionMetadata.confidence * 100)}% confidence
                        </span>
                      )}
                    </div>
                    
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => setShowVisionDetails(!showVisionDetails)}
                      className="h-auto p-1 text-muted-foreground hover:text-foreground"
                    >
                      {showVisionDetails ? (
                        <ChevronUp className="w-4 h-4" />
                      ) : (
                        <ChevronDown className="w-4 h-4" />
                      )}
                    </Button>
                  </div>
                  
                  {/* Expandable Details */}
                  {showVisionDetails && (
                    <div className="pt-2 border-t border-border space-y-2">
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
                        {message.visionMetadata?.analysisType && (
                          <div className="flex items-center gap-1">
                            <Eye className="w-3 h-3 text-muted-foreground" />
                            <span className="capitalize">{message.visionMetadata?.analysisType}</span>
                          </div>
                        )}
                        
                        {message.visionMetadata?.processingTime && (
                          <div className="flex items-center gap-1">
                            <Clock className="w-3 h-3 text-muted-foreground" />
                            <span>{message.visionMetadata?.processingTime?.toFixed(1)}s</span>
                          </div>
                        )}
                        
                        {message.visionMetadata?.cost && (
                          <div className="flex items-center gap-1">
                            <DollarSign className="w-3 h-3 text-muted-foreground" />
                            <span>${message.visionMetadata?.cost?.toFixed(3)}</span>
                          </div>
                        )}
                        
                        <div className="flex items-center gap-1">
                          <Badge
                            variant={message.visionMetadata?.modelUsed?.toLowerCase().includes('gpt-5') ? 'default' : 'secondary'}
                            className="text-xs"
                          >
                            ✨ {message.visionMetadata?.modelUsed || 'Vision Model'}
                          </Badge>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
        
        <div className="flex items-center gap-2 mt-1">
          <span className="text-xs text-muted-foreground">
            {(message.timestamp instanceof Date ? message.timestamp : new Date(message.timestamp)).toLocaleTimeString()}
          </span>
          
          {message.status === 'pending' && (
            <Badge variant="outline" className="text-xs px-1.5 py-0.5">
              <div className="w-1.5 h-1.5 bg-yellow-500 rounded-full animate-pulse mr-1" />
              Sending
            </Badge>
          )}
          
          {message.status === 'error' && (
            <Badge variant="destructive" className="text-xs px-1.5 py-0.5">
              <div className="w-1.5 h-1.5 bg-red-500 rounded-full mr-1" />
              Failed
            </Badge>
          )}
          
          {message.status === 'delivered' && isUser && (
            <div className="w-1.5 h-1.5 bg-green-500 rounded-full" />
          )}
        </div>
      </div>
      
      {isUser && (
        <Avatar className="w-8 h-8 flex-shrink-0">
          <AvatarFallback className="bg-gray-600 text-white text-sm font-medium">
            {config?.icon || '👤'}
          </AvatarFallback>
        </Avatar>
      )}
    </div>
  )
}