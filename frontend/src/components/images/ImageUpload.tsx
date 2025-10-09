'use client'

import React, { useState, useCallback } from 'react'
import Image from 'next/image'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Checkbox } from '@/components/ui/checkbox'
import { Progress } from '@/components/ui/progress'
import { Badge } from '@/components/ui/badge'
import { 
  Upload, 
  X, 
  Image as ImageIcon, 
  AlertCircle,
  Plus
} from 'lucide-react'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { imagesAPI, ImageUploadResponse, UploadProgress } from '@/lib/api/images'

interface ImageUploadProps {
  onUploadSuccess: (response: ImageUploadResponse) => void
  onUploadError: (error: string) => void
  className?: string
}

interface FileWithPreview extends File {
  preview?: string
}

export function ImageUpload({ onUploadSuccess, onUploadError, className = '' }: ImageUploadProps) {
  const [files, setFiles] = useState<FileWithPreview[]>([])
  const [description, setDescription] = useState('')
  const [tags, setTags] = useState<string[]>([])
  const [newTag, setNewTag] = useState('')
  const [isPublic, setIsPublic] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState<UploadProgress | null>(null)
  const [dragActive, setDragActive] = useState(false)
  const [validationError, setValidationError] = useState<string | null>(null)

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true)
    } else if (e.type === 'dragleave') {
      setDragActive(false)
    }
  }, [])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFiles(Array.from(e.dataTransfer.files))
    }
  }, [])

  const handleFiles = (fileList: File[]) => {
    setValidationError(null)
    
    const validFiles: FileWithPreview[] = []
    
    for (const file of fileList) {
      const validation = imagesAPI.validateFile(file)
      
      if (!validation.valid) {
        setValidationError(validation.error || 'Invalid file')
        return
      }
      
      const fileWithPreview = file as FileWithPreview
      fileWithPreview.preview = URL.createObjectURL(file)
      validFiles.push(fileWithPreview)
    }
    
    setFiles(validFiles)
  }

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      handleFiles(Array.from(e.target.files))
    }
  }

  const removeFile = (index: number) => {
    setFiles(prev => {
      const newFiles = [...prev]
      if (newFiles[index].preview) {
        URL.revokeObjectURL(newFiles[index].preview!)
      }
      newFiles.splice(index, 1)
      return newFiles
    })
  }

  const addTag = () => {
    const trimmedTag = newTag.trim().toLowerCase()
    if (trimmedTag && !tags.includes(trimmedTag) && tags.length < 10) {
      setTags(prev => [...prev, trimmedTag])
      setNewTag('')
    }
  }

  const removeTag = (tagToRemove: string) => {
    setTags(prev => prev.filter(tag => tag !== tagToRemove))
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault()
      addTag()
    }
  }

  const handleUpload = async () => {
    if (files.length === 0) return

    setUploading(true)
    setUploadProgress(null)

    try {
      // For now, upload one file at a time
      const file = files[0]
      
      const response = await imagesAPI.uploadImage(file, {
        description: description.trim() || undefined,
        tags: tags.length > 0 ? tags : undefined,
        public: isPublic,
        onProgress: setUploadProgress
      })

      onUploadSuccess(response)
      
      // Reset form
      setFiles([])
      setDescription('')
      setTags([])
      setNewTag('')
      setIsPublic(false)
      setUploadProgress(null)
      
    } catch (error) {
      console.error('Upload error:', error)
      const errorMessage = error instanceof Error ? error.message : 'Upload failed'
      onUploadError(errorMessage)
    } finally {
      setUploading(false)
    }
  }

  // Cleanup preview URLs on unmount
  React.useEffect(() => {
    return () => {
      files.forEach(file => {
        if (file.preview) {
          URL.revokeObjectURL(file.preview)
        }
      })
    }
  }, [files])

  return (
    <Card className={className}>
      <CardContent className="p-6">
        <div className="space-y-6">
          {/* File Drop Zone */}
          <div
            className={`border-2 border-dashed rounded-lg p-6 text-center transition-colors ${
              dragActive 
                ? 'border-primary bg-primary/5' 
                : 'border-border hover:border-primary/50'
            }`}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
          >
            <div className="space-y-4">
              <div className="mx-auto h-12 w-12 rounded-full bg-muted flex items-center justify-center">
                <Upload className="h-6 w-6 text-muted-foreground" />
              </div>
              
              <div>
                <p className="text-lg font-medium">Drop your images here</p>
                <p className="text-sm text-muted-foreground">
                  or click to browse files
                </p>
              </div>
              
              <div className="flex flex-col sm:flex-row gap-2 items-center justify-center">
                <Button
                  variant="outline"
                  onClick={() => document.getElementById('file-input')?.click()}
                  disabled={uploading}
                >
                  <ImageIcon className="mr-2 h-4 w-4" />
                  Select Images
                </Button>
                <span className="text-xs text-muted-foreground">
                  JPEG, PNG, WebP • Max 10MB
                </span>
              </div>
              
              <input
                id="file-input"
                type="file"
                accept="image/jpeg,image/png,image/webp"
                multiple
                className="hidden"
                onChange={handleFileInput}
                disabled={uploading}
              />
            </div>
          </div>

          {/* Validation Error */}
          {validationError && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{validationError}</AlertDescription>
            </Alert>
          )}

          {/* File Preview */}
          {files.length > 0 && (
            <div className="space-y-4">
              <Label>Selected Files</Label>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {files.map((file, index) => (
                  <div key={index} className="relative">
                    <Card>
                      <CardContent className="p-3">
                        <div className="space-y-2">
                          {file.preview && (
                            <div className="aspect-square relative rounded overflow-hidden bg-muted">
                              <Image 
                                src={file.preview} 
                                alt={file.name}
                                fill
                                className="object-cover"
                                sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
                              />
                            </div>
                          )}
                          <div className="space-y-1">
                            <p className="text-sm font-medium truncate" title={file.name}>
                              {file.name}
                            </p>
                            <p className="text-xs text-muted-foreground">
                              {imagesAPI.formatFileSize(file.size)}
                            </p>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                    
                    <Button
                      size="sm"
                      variant="destructive"
                      className="absolute -top-2 -right-2 h-6 w-6 p-0 rounded-full"
                      onClick={() => removeFile(index)}
                      disabled={uploading}
                    >
                      <X className="h-3 w-3" />
                    </Button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Metadata Form */}
          {files.length > 0 && (
            <div className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="description">Description (optional)</Label>
                <Textarea
                  id="description"
                  placeholder="Describe your image..."
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  maxLength={500}
                  disabled={uploading}
                />
                <p className="text-xs text-muted-foreground">
                  {description.length}/500 characters
                </p>
              </div>

              <div className="space-y-2">
                <Label>Tags (optional)</Label>
                <div className="flex gap-2">
                  <Input
                    placeholder="Add tag..."
                    value={newTag}
                    onChange={(e) => setNewTag(e.target.value)}
                    onKeyPress={handleKeyPress}
                    disabled={uploading || tags.length >= 10}
                  />
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={addTag}
                    disabled={!newTag.trim() || tags.length >= 10 || uploading}
                  >
                    <Plus className="h-4 w-4" />
                  </Button>
                </div>
                
                {tags.length > 0 && (
                  <div className="flex flex-wrap gap-1">
                    {tags.map((tag) => (
                      <Badge key={tag} variant="secondary" className="text-xs">
                        {tag}
                        <Button
                          size="sm"
                          variant="ghost"
                          className="ml-1 h-auto p-0 hover:bg-transparent"
                          onClick={() => removeTag(tag)}
                          disabled={uploading}
                        >
                          <X className="h-3 w-3" />
                        </Button>
                      </Badge>
                    ))}
                  </div>
                )}
                
                <p className="text-xs text-muted-foreground">
                  {tags.length}/10 tags
                </p>
              </div>

              <div className="flex items-center space-x-2">
                <Checkbox
                  id="public"
                  checked={isPublic}
                  onCheckedChange={(checked) => setIsPublic(checked === true)}
                  disabled={uploading}
                />
                <Label htmlFor="public" className="text-sm">
                  Make this image publicly accessible
                </Label>
              </div>
            </div>
          )}

          {/* Upload Progress */}
          {uploadProgress && (
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span>Uploading...</span>
                <span>{uploadProgress.percentage}%</span>
              </div>
              <Progress value={uploadProgress.percentage} />
            </div>
          )}

          {/* Upload Button */}
          {files.length > 0 && (
            <Button 
              onClick={handleUpload} 
              disabled={uploading}
              className="w-full"
            >
              {uploading ? (
                <>
                  <div className="mr-2 h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
                  Uploading...
                </>
              ) : (
                <>
                  <Upload className="mr-2 h-4 w-4" />
                  Upload {files.length} {files.length === 1 ? 'Image' : 'Images'}
                </>
              )}
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  )
}