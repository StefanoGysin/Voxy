'use client'

import { useState, useRef, useCallback } from 'react'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { cn } from '@/lib/utils'
import { Send, Loader2, Image as ImageIcon, X } from 'lucide-react'
import Image from 'next/image'
import { AgentSelector } from './agent-selector'
import { ImageUpload } from './image-upload'
import type { ImageUpload as ImageUploadType } from '@/types'

interface MessageInputProps {
  onSendMessage: (message: string, selectedAgent?: string, imageUrl?: string) => void
  disabled?: boolean
  className?: string
  placeholder?: string
}

export function MessageInput({ 
  onSendMessage, 
  disabled = false, 
  className,
  placeholder = "Type your message to VOXY..."
}: MessageInputProps) {
  const [message, setMessage] = useState('')
  const [isComposing, setIsComposing] = useState(false)
  const [selectedAgent, setSelectedAgent] = useState('voxy')
  const [currentPrompt, setCurrentPrompt] = useState('')
  const [showImageUpload, setShowImageUpload] = useState(false)
  const [attachedImage, setAttachedImage] = useState<string | null>(null)
  const [imagePreview, setImagePreview] = useState<string | null>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const handleSubmit = useCallback(() => {
    console.log('🔍 DEBUG - handleSubmit called:', { message: message.trim(), attachedImage, selectedAgent })

    if ((message.trim() || attachedImage) && !disabled) {
      // Only prefix with agent name when:
      // 1. Agent is not VOXY AND
      // 2. Agent is not Vision (Vision uses image_url parameter, not prefix)
      const shouldPrefixAgent = selectedAgent !== 'voxy' && selectedAgent !== 'vision'

      const finalMessage = shouldPrefixAgent
        ? `[${selectedAgent.toUpperCase()}] ${message.trim()}`
        : message.trim()

      // Auto-select Vision Agent if image is attached and no specific agent selected
      const agentToUse = attachedImage && selectedAgent === 'voxy' ? 'vision' : selectedAgent

      console.log('🔍 DEBUG - Calling onSendMessage:', { finalMessage, agentToUse, attachedImage })
      onSendMessage(finalMessage, agentToUse, attachedImage || undefined)
      setMessage('')
      setCurrentPrompt('')
      setAttachedImage(null)
      setImagePreview(null)
      setShowImageUpload(false)
      
      // Reset textarea height
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto'
      }
    }
  }, [message, attachedImage, disabled, onSendMessage, selectedAgent])

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey && !isComposing) {
      e.preventDefault()
      handleSubmit()
    }
  }, [handleSubmit, isComposing])

  const handleTextareaChange = useCallback((e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const value = e.target.value
    setMessage(value)

    // Auto-resize textarea
    const textarea = e.target
    textarea.style.height = 'auto'
    textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px'
  }, [])

  const canSend = (message.trim().length > 0 || attachedImage) && !disabled

  const handleAgentSelect = useCallback((agent: { id: string; prompt: string }) => {
    setSelectedAgent(agent.id)
    setCurrentPrompt(agent.prompt)
    
    // Focus textarea when agent is selected
    if (textareaRef.current) {
      textareaRef.current.focus()
    }
  }, [])

  const handleImageSelect = useCallback((imageUrl: string) => {
    console.log('🔍 DEBUG - handleImageSelect called with URL:', imageUrl)
    setAttachedImage(imageUrl)
    setImagePreview(imageUrl)
    setShowImageUpload(false)
    
    // Auto-select Vision Agent when image is attached
    if (selectedAgent === 'voxy') {
      setSelectedAgent('vision')
      console.log('🔍 DEBUG - Auto-selected vision agent')
    }
  }, [selectedAgent])

  const handleImageUpload = useCallback((upload: ImageUploadType) => {
    console.log('🔍 DEBUG - handleImageUpload called:', upload)
    if (upload.uploadedUrl) {
      console.log('🔍 DEBUG - Upload has URL, calling handleImageSelect')
      handleImageSelect(upload.uploadedUrl)
    } else {
      console.log('⚠️ DEBUG - Upload has no URL!', upload)
    }
  }, [handleImageSelect])

  const handleRemoveImage = useCallback(() => {
    setAttachedImage(null)
    setImagePreview(null)
    
    // Revert to VOXY if Vision Agent was auto-selected
    if (selectedAgent === 'vision') {
      setSelectedAgent('voxy')
    }
  }, [selectedAgent])

  const displayPlaceholder = attachedImage 
    ? "Describe what you want to analyze in this image..."
    : currentPrompt || (disabled ? 'Connecting to VOXY...' : placeholder)

  return (
    <div className={cn('bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60', className)}>
      <div className="container max-w-4xl mx-auto px-3 sm:px-4 pt-3 pb-4 space-y-3">
        {/* Agent Selector - Responsive */}
        <div className="hidden sm:block">
          <AgentSelector 
            onSelectAgent={handleAgentSelect}
            selectedAgent={selectedAgent}
          />
        </div>
        
        {/* Image Preview */}
        {imagePreview && (
          <div className="flex items-center gap-3 p-3 bg-muted/50 rounded-lg">
            <div className="relative w-16 h-16 rounded-lg overflow-hidden flex-shrink-0">
              <Image 
                src={imagePreview} 
                alt="Attached" 
                fill
                className="object-cover"
              />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-foreground">Image attached</p>
              <p className="text-xs text-muted-foreground">
                Will be analyzed by Vision Agent
              </p>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={handleRemoveImage}
              className="h-auto p-2 text-muted-foreground hover:text-foreground"
            >
              <X className="w-4 h-4" />
            </Button>
          </div>
        )}

        {/* Image Upload Component */}
        {showImageUpload && (
          <div className="border rounded-lg p-3 sm:p-4 bg-muted/20">
            <div className="flex items-center justify-between mb-3">
              <h4 className="text-sm font-medium">Upload Image for Analysis</h4>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowImageUpload(false)}
                className="h-auto p-2 touch-manipulation"
              >
                <X className="w-4 h-4" />
              </Button>
            </div>
            <ImageUpload
              onImageSelect={handleImageSelect}
              onImageUpload={handleImageUpload}
              disabled={disabled}
              maxSizeMB={10}
            />
          </div>
        )}

        {/* Main Input Row */}
        <div className="flex items-end gap-3">
          {/* Mobile Avatar */}
          <div className="hidden sm:flex shrink-0 w-8 h-8 bg-gradient-to-br from-purple-500 to-pink-500 rounded-full items-center justify-center">
            <span className="text-sm font-medium text-white">N</span>
          </div>
          
          <div className="flex-1 relative">
            <Textarea
              ref={textareaRef}
              value={message}
              onChange={handleTextareaChange}
              onKeyDown={handleKeyDown}
              onCompositionStart={() => setIsComposing(true)}
              onCompositionEnd={() => setIsComposing(false)}
              placeholder={displayPlaceholder}
              disabled={disabled}
              className={cn(
                'resize-none border-0 shadow-sm rounded-lg',
                'bg-muted/50 focus:bg-background',
                'min-h-[44px] max-h-[80px] sm:max-h-[120px]',
                'transition-colors duration-200',
                'text-sm sm:text-base',
                'px-3 py-3 sm:px-4 sm:py-3'
              )}
              rows={1}
            />
            
            {/* Mobile Agent Selector - Bottom Sheet Style */}
            <div className="sm:hidden mt-2">
              <AgentSelector 
                onSelectAgent={handleAgentSelect}
                selectedAgent={selectedAgent}
              />
            </div>
          </div>
          
          <div className="flex items-center gap-2">
            {/* Image Upload Button */}
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowImageUpload(!showImageUpload)}
              disabled={disabled}
              className={cn(
                'h-11 w-11 shrink-0 rounded-full touch-manipulation',
                'hover:bg-muted active:bg-muted',
                showImageUpload && 'bg-muted'
              )}
              title="Upload image for analysis"
            >
              <ImageIcon className="h-4 w-4" />
            </Button>
            
            {/* Send Button */}
            <Button
              onClick={handleSubmit}
              disabled={!canSend}
              size="sm"
              className={cn(
                'h-11 w-11 shrink-0 rounded-full touch-manipulation',
                'transition-all duration-200',
                canSend 
                  ? 'bg-primary hover:bg-primary/90 active:bg-primary/80 text-primary-foreground' 
                  : 'bg-muted text-muted-foreground cursor-not-allowed'
              )}
            >
              {disabled ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Send className="h-4 w-4" />
              )}
            </Button>
          </div>
        </div>
        
        {/* Hints - Only on desktop */}
        <div className="hidden sm:flex items-center justify-between text-xs text-muted-foreground">
          <div className="flex items-center gap-4">
            {!disabled && (
              <span>Press Enter to send, Shift+Enter for new line • Click 📷 to upload images</span>
            )}
          </div>
          
          {message.length > 0 && (
            <span className={cn(
              message.length > 1000 ? 'text-destructive' : 'text-muted-foreground'
            )}>
              {message.length}/2000
            </span>
          )}
        </div>
      </div>
    </div>
  )
}