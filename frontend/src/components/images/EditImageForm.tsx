'use client'

import React, { useState } from 'react'
import { 
  Dialog, 
  DialogContent, 
  DialogHeader, 
  DialogTitle,
  DialogFooter 
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Checkbox } from '@/components/ui/checkbox'
import { Badge } from '@/components/ui/badge'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { 
  Save, 
  X, 
  Plus, 
  AlertCircle,
  Loader2
} from 'lucide-react'
import { ImageDetailResponse, ImageListResponse, ImageMetadataUpdate } from '@/lib/api/images'
import { imagesAPI } from '@/lib/api/images'

interface EditImageFormProps {
  image: ImageListResponse | ImageDetailResponse | null
  open: boolean
  onClose: () => void
  onSuccess: (updatedImage: ImageDetailResponse) => void
  onError: (error: string) => void
}

export function EditImageForm({ image, open, onClose, onSuccess, onError }: EditImageFormProps) {
  const [description, setDescription] = useState('')
  const [tags, setTags] = useState<string[]>([])
  const [newTag, setNewTag] = useState('')
  const [isPublic, setIsPublic] = useState(false)
  const [loading, setLoading] = useState(false)
  const [validationError, setValidationError] = useState<string | null>(null)

  // Initialize form when image changes
  React.useEffect(() => {
    if (image) {
      setDescription(image.description || '')
      setTags(image.tags || [])
      setIsPublic(image.public)
      setValidationError(null)
    }
  }, [image])

  const addTag = () => {
    const trimmedTag = newTag.trim().toLowerCase()
    if (trimmedTag && !tags.includes(trimmedTag) && tags.length < 10) {
      setTags(prev => [...prev, trimmedTag])
      setNewTag('')
      setValidationError(null)
    } else if (tags.length >= 10) {
      setValidationError('Maximum of 10 tags allowed')
    }
  }

  const removeTag = (tagToRemove: string) => {
    setTags(prev => prev.filter(tag => tag !== tagToRemove))
    setValidationError(null)
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault()
      addTag()
    }
  }

  const handleSave = async () => {
    if (!image) return

    setLoading(true)
    setValidationError(null)

    try {
      const updates: ImageMetadataUpdate = {
        description: description.trim() || undefined,
        tags: tags.length > 0 ? tags : undefined,
        public: isPublic
      }

      const updatedImage = await imagesAPI.updateImage(image.id, updates)
      onSuccess(updatedImage)
      onClose()
    } catch (error) {
      console.error('Update error:', error)
      const errorMessage = error instanceof Error ? error.message : 'Failed to update image'
      onError(errorMessage)
      setValidationError(errorMessage)
    } finally {
      setLoading(false)
    }
  }

  const handleClose = () => {
    if (!loading) {
      onClose()
    }
  }

  if (!image) return null

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>Edit Image</DialogTitle>
        </DialogHeader>

        <div className="space-y-6">
          {/* File Name Display */}
          <div className="space-y-2">
            <Label>File Name</Label>
            <div className="p-2 bg-muted rounded text-sm truncate" title={image.file_name}>
              {image.file_name}
            </div>
          </div>

          {/* Description */}
          <div className="space-y-2">
            <Label htmlFor="edit-description">Description</Label>
            <Textarea
              id="edit-description"
              placeholder="Describe your image..."
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              maxLength={500}
              disabled={loading}
              rows={3}
            />
            <p className="text-xs text-muted-foreground">
              {description.length}/500 characters
            </p>
          </div>

          {/* Tags */}
          <div className="space-y-2">
            <Label>Tags</Label>
            <div className="flex gap-2">
              <Input
                placeholder="Add tag..."
                value={newTag}
                onChange={(e) => setNewTag(e.target.value)}
                onKeyPress={handleKeyPress}
                disabled={loading || tags.length >= 10}
              />
              <Button
                size="sm"
                variant="outline"
                onClick={addTag}
                disabled={!newTag.trim() || tags.length >= 10 || loading}
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
                      disabled={loading}
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

          {/* Public Toggle */}
          <div className="flex items-center space-x-2">
            <Checkbox
              id="edit-public"
              checked={isPublic}
              onCheckedChange={(checked) => setIsPublic(checked === true)}
              disabled={loading}
            />
            <Label htmlFor="edit-public" className="text-sm">
              Make this image publicly accessible
            </Label>
          </div>

          {/* Validation Error */}
          {validationError && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{validationError}</AlertDescription>
            </Alert>
          )}
        </div>

        <DialogFooter>
          <Button
            variant="outline"
            onClick={handleClose}
            disabled={loading}
          >
            Cancel
          </Button>
          <Button
            onClick={handleSave}
            disabled={loading}
          >
            {loading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Saving...
              </>
            ) : (
              <>
                <Save className="mr-2 h-4 w-4" />
                Save Changes
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}