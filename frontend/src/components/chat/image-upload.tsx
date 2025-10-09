'use client'

import { useState, useRef, useCallback } from 'react'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import { Upload, X, AlertCircle, Check } from 'lucide-react'
import Image from 'next/image'
import { useVisionStore } from '@/lib/store/vision-store'
import { useAuthStore } from '@/lib/store/auth-store'
import type { ImageUpload } from '@/types'

interface ImageUploadProps {
  onImageSelect?: (imageUrl: string) => void
  onImageUpload?: (upload: ImageUpload) => void
  className?: string
  disabled?: boolean
  maxSizeMB?: number
  acceptedTypes?: string[]
}

export function ImageUpload({ 
  onImageSelect,
  onImageUpload,
  className,
  disabled = false,
  maxSizeMB = 10,
  acceptedTypes = ['image/jpeg', 'image/png', 'image/webp']
}: ImageUploadProps) {
  const [isDragOver, setIsDragOver] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  
  const { 
    uploadedImages, 
    isUploading, 
    uploadProgress,
    addImageUpload,
    updateImageUpload,
    removeImageUpload,
    setIsUploading,
    setUploadProgress
  } = useVisionStore()

  const validateFile = useCallback((file: File): string | null => {
    // Check file type
    if (!acceptedTypes.includes(file.type)) {
      return `File type ${file.type} not supported. Please use JPEG, PNG, or WebP.`
    }
    
    // Check file size
    const maxSizeBytes = maxSizeMB * 1024 * 1024
    if (file.size > maxSizeBytes) {
      return `File size ${(file.size / 1024 / 1024).toFixed(1)}MB exceeds limit of ${maxSizeMB}MB.`
    }
    
    // Check minimum size (1KB)
    if (file.size < 1024) {
      return 'File is too small. Minimum size is 1KB.'
    }
    
    return null
  }, [acceptedTypes, maxSizeMB])

  const createImagePreview = useCallback((file: File): Promise<string> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader()
      reader.onload = (e) => resolve(e.target?.result as string)
      reader.onerror = () => reject(new Error('Failed to read file'))
      reader.readAsDataURL(file)
    })
  }, [])

  const uploadImageFile = async (file: File): Promise<string> => {
    const formData = new FormData()
    formData.append('file', file)
    
    // Get JWT token for authentication
    const { token } = useAuthStore.getState()
    
    const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/images/upload`, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${token}`
      },
      body: formData
    })
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      throw new Error(errorData.detail || `Upload failed: ${response.status}`)
    }
    
    const result = await response.json()
    return result.url
  }

  const handleFiles = useCallback(async (files: File[]) => {
    if (disabled || files.length === 0) return
    
    setError(null)
    
    for (const file of files) {
      const validationError = validateFile(file)
      if (validationError) {
        setError(validationError)
        continue
      }
      
      // Create upload object outside try block for error handling
      let upload: ImageUpload | null = null
      
      try {
        // Create preview
        const preview = await createImagePreview(file)
        
        // Create upload object
        upload = {
          id: crypto.randomUUID(),
          file,
          preview,
          status: 'uploading',
          progress: 0
        }
        
        addImageUpload(upload)
        setIsUploading(true)
        
        // Simulate upload progress
        let currentProgress = 0
        const progressInterval = setInterval(() => {
          currentProgress += Math.random() * 30
          if (currentProgress >= 95) {
            clearInterval(progressInterval)
            currentProgress = 95
          }
          setUploadProgress(currentProgress)
        }, 200)
        
        // Upload to backend
        const uploadedUrl = await uploadImageFile(file)
        
        // Complete upload
        clearInterval(progressInterval)
        setUploadProgress(100)
        
        const completedUpload = {
          ...upload,
          status: 'uploaded' as const,
          progress: 100,
          uploadedUrl
        }
        
        updateImageUpload(upload.id, completedUpload)
        
        // Notify parent components
        onImageUpload?.(completedUpload)
        onImageSelect?.(uploadedUrl)
        
        setIsUploading(false)
        setUploadProgress(0)
        
      } catch (error) {
        console.error('Upload failed:', error)
        if (upload) {
          updateImageUpload(upload.id, { 
            status: 'error',
            progress: 0 
          })
        }
        setError(error instanceof Error ? error.message : 'Upload failed')
        setIsUploading(false)
        setUploadProgress(0)
      }
    }
  }, [disabled, validateFile, createImagePreview, addImageUpload, updateImageUpload, onImageUpload, onImageSelect, setIsUploading, setUploadProgress])

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    if (!disabled) {
      setIsDragOver(true)
    }
  }, [disabled])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(false)
  }, [])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(false)
    
    if (disabled) return
    
    const files = Array.from(e.dataTransfer.files)
    handleFiles(files)
  }, [disabled, handleFiles])

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || [])
    handleFiles(files)
    
    // Reset input
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }, [handleFiles])

  const handleRemoveImage = useCallback((uploadId: string) => {
    removeImageUpload(uploadId)
  }, [removeImageUpload])

  const handleSelectExisting = useCallback((upload: ImageUpload) => {
    if (upload.uploadedUrl) {
      onImageSelect?.(upload.uploadedUrl)
    }
  }, [onImageSelect])

  return (
    <div className={cn('space-y-4', className)}>
      {/* Upload Area */}
      <div
        className={cn(
          'relative border-2 border-dashed rounded-lg p-6 transition-all duration-200',
          'hover:border-primary/50 focus-within:border-primary',
          isDragOver && 'border-primary bg-primary/5',
          disabled && 'opacity-50 cursor-not-allowed',
          !disabled && 'cursor-pointer',
          error && 'border-destructive'
        )}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => !disabled && fileInputRef.current?.click()}
      >
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept={acceptedTypes.join(',')}
          onChange={handleFileSelect}
          className="hidden"
          disabled={disabled}
        />
        
        <div className="flex flex-col items-center text-center space-y-3">
          <div className={cn(
            'w-12 h-12 rounded-full flex items-center justify-center',
            'bg-muted text-muted-foreground',
            isDragOver && 'bg-primary text-primary-foreground'
          )}>
            <Upload className="w-6 h-6" />
          </div>
          
          <div className="space-y-1">
            <p className={cn(
              'text-sm font-medium',
              isDragOver && 'text-primary'
            )}>
              {isDragOver ? 'Drop images here' : 'Upload images for analysis'}
            </p>
            <p className="text-xs text-muted-foreground">
              Drag & drop or click to select • JPEG, PNG, WebP • Max {maxSizeMB}MB
            </p>
          </div>
          
          {isUploading && (
            <div className="w-full max-w-xs space-y-2">
              <div className="h-1 bg-muted rounded-full overflow-hidden">
                <div 
                  className="h-full bg-primary transition-all duration-300"
                  style={{ width: `${uploadProgress}%` }}
                />
              </div>
              <p className="text-xs text-muted-foreground">
                Uploading... {Math.round(uploadProgress)}%
              </p>
            </div>
          )}
        </div>
      </div>
      
      {/* Error Display */}
      {error && (
        <div className="flex items-center gap-2 p-3 bg-destructive/10 border border-destructive/20 rounded-lg">
          <AlertCircle className="w-4 h-4 text-destructive" />
          <span className="text-sm text-destructive">{error}</span>
          <Button 
            variant="ghost" 
            size="sm"
            onClick={() => setError(null)}
            className="ml-auto h-auto p-1 text-destructive hover:text-destructive"
          >
            <X className="w-3 h-3" />
          </Button>
        </div>
      )}
      
      {/* Uploaded Images Grid */}
      {uploadedImages.length > 0 && (
        <div className="space-y-2">
          <h4 className="text-sm font-medium text-foreground">Recent Uploads</h4>
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2 sm:gap-3">
            {uploadedImages.slice(-6).map((upload) => (
              <div 
                key={upload.id} 
                className={cn(
                  'relative group aspect-square rounded-lg overflow-hidden border',
                  'hover:border-primary transition-colors',
                  upload.status === 'uploaded' && 'cursor-pointer'
                )}
                onClick={() => upload.status === 'uploaded' && handleSelectExisting(upload)}
              >
                <Image 
                  src={upload.preview} 
                  alt="Uploaded" 
                  fill
                  className="object-cover"
                />
                
                {/* Status Overlay */}
                <div className="absolute inset-0 bg-black/50 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                  {upload.status === 'uploading' && (
                    <div className="text-white text-center">
                      <Upload className="w-4 h-4 animate-spin mx-auto mb-1" />
                      <span className="text-xs">{upload.progress || 0}%</span>
                    </div>
                  )}
                  {upload.status === 'uploaded' && (
                    <div className="text-white text-center">
                      <Check className="w-4 h-4 mx-auto mb-1" />
                      <span className="text-xs">Click to use</span>
                    </div>
                  )}
                  {upload.status === 'error' && (
                    <div className="text-red-400 text-center">
                      <AlertCircle className="w-4 h-4 mx-auto mb-1" />
                      <span className="text-xs">Failed</span>
                    </div>
                  )}
                </div>
                
                {/* Remove Button */}
                <Button
                  variant="destructive"
                  size="sm"
                  className="absolute top-1 right-1 h-6 w-6 p-0 opacity-0 group-hover:opacity-100 transition-opacity"
                  onClick={(e) => {
                    e.stopPropagation()
                    handleRemoveImage(upload.id)
                  }}
                >
                  <X className="w-3 h-3" />
                </Button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}