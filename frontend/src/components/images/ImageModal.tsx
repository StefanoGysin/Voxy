'use client'

import { useState } from 'react'
import Image from 'next/image'
import { 
  Dialog, 
  DialogContent, 
  DialogHeader, 
  DialogTitle,
  DialogDescription 
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Separator } from '@/components/ui/separator'
import { 
  Download, 
  Copy, 
  Edit, 
  Trash2, 
  ExternalLink,
  Calendar,
  FileText,
  Eye,
  X
} from 'lucide-react'
import { ImageDetailResponse, ImageListResponse } from '@/lib/api/images'
import { imagesAPI } from '@/lib/api/images'

interface ImageModalProps {
  image: ImageListResponse | ImageDetailResponse | null
  open: boolean
  onClose: () => void
  onEdit: (image: ImageListResponse | ImageDetailResponse) => void
  onDelete: (image: ImageListResponse | ImageDetailResponse) => void
}

export function ImageModal({ image, open, onClose, onEdit, onDelete }: ImageModalProps) {
  const [imageLoading, setImageLoading] = useState(true)
  const [imageError, setImageError] = useState(false)

  if (!image) return null

  const handleCopyUrl = async () => {
    try {
      await navigator.clipboard.writeText(image.url)
      // In a real app, you'd show a toast notification
      console.log('Image URL copied to clipboard')
    } catch (error) {
      console.error('Failed to copy URL:', error)
    }
  }

  const handleDownload = () => {
    const link = document.createElement('a')
    link.href = image.url
    link.download = image.file_name
    link.target = '_blank'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const isDetailResponse = (img: ImageListResponse | ImageDetailResponse): img is ImageDetailResponse => {
    return 'storage_path' in img
  }

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl h-[90vh] p-0">
        <div className="grid grid-cols-1 lg:grid-cols-3 h-full">
          {/* Image Display */}
          <div className="lg:col-span-2 relative bg-black">
            {!imageError ? (
              <div className="relative w-full h-full">
                <Image
                  src={image.url}
                  alt={image.description || image.file_name}
                  fill
                  className={`object-contain ${imageLoading ? 'blur-sm' : ''}`}
                  onLoad={() => setImageLoading(false)}
                  onError={() => {
                    setImageError(true)
                    setImageLoading(false)
                  }}
                  sizes="(max-width: 1024px) 100vw, 66vw"
                />
                
                {/* Loading Overlay */}
                {imageLoading && (
                  <div className="absolute inset-0 flex items-center justify-center bg-black/50">
                    <div className="h-8 w-8 animate-spin rounded-full border-2 border-white border-t-transparent" />
                  </div>
                )}
              </div>
            ) : (
              <div className="flex h-full w-full items-center justify-center bg-muted">
                <div className="text-center space-y-2">
                  <FileText className="h-12 w-12 text-muted-foreground mx-auto" />
                  <p className="text-muted-foreground">Failed to load image</p>
                </div>
              </div>
            )}

            {/* Close Button */}
            <Button
              size="sm"
              variant="secondary"
              className="absolute top-4 right-4 h-8 w-8 p-0"
              onClick={onClose}
            >
              <X className="h-4 w-4" />
            </Button>
          </div>

          {/* Image Details Panel */}
          <div className="border-l bg-background">
            <DialogHeader className="p-6 pb-4">
              <DialogTitle className="text-lg truncate" title={image.file_name}>
                {image.file_name}
              </DialogTitle>
              {image.description && (
                <DialogDescription className="text-sm">
                  {image.description}
                </DialogDescription>
              )}
            </DialogHeader>

            <ScrollArea className="h-[calc(100%-8rem)]">
              <div className="p-6 pt-0 space-y-6">
                {/* Action Buttons */}
                <div className="flex flex-wrap gap-2">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => onEdit(image)}
                  >
                    <Edit className="mr-2 h-4 w-4" />
                    Edit
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={handleCopyUrl}
                  >
                    <Copy className="mr-2 h-4 w-4" />
                    Copy URL
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={handleDownload}
                  >
                    <Download className="mr-2 h-4 w-4" />
                    Download
                  </Button>
                </div>

                <Separator />

                {/* File Information */}
                <div className="space-y-4">
                  <h4 className="text-sm font-medium">File Information</h4>
                  <div className="space-y-3 text-sm">
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Size</span>
                      <span>{imagesAPI.formatFileSize(image.file_size)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Type</span>
                      <span>{image.content_type}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Visibility</span>
                      <Badge variant={image.public ? "default" : "secondary"}>
                        {image.public ? (
                          <>
                            <ExternalLink className="mr-1 h-3 w-3" />
                            Public
                          </>
                        ) : (
                          <>
                            <Eye className="mr-1 h-3 w-3" />
                            Private
                          </>
                        )}
                      </Badge>
                    </div>
                    {isDetailResponse(image) && (
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Storage Path</span>
                        <span className="text-xs font-mono truncate" title={image.storage_path}>
                          {image.storage_path}
                        </span>
                      </div>
                    )}
                  </div>
                </div>

                <Separator />

                {/* Dates */}
                <div className="space-y-4">
                  <h4 className="text-sm font-medium">Dates</h4>
                  <div className="space-y-3 text-sm">
                    <div className="flex justify-between items-start">
                      <span className="text-muted-foreground">Created</span>
                      <div className="text-right">
                        <div className="flex items-center">
                          <Calendar className="mr-1 h-3 w-3" />
                          {formatDate(image.created_at)}
                        </div>
                      </div>
                    </div>
                    <div className="flex justify-between items-start">
                      <span className="text-muted-foreground">Updated</span>
                      <div className="text-right">
                        <div className="flex items-center">
                          <Calendar className="mr-1 h-3 w-3" />
                          {formatDate(image.updated_at)}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Tags */}
                {image.tags && image.tags.length > 0 && (
                  <>
                    <Separator />
                    <div className="space-y-4">
                      <h4 className="text-sm font-medium">Tags</h4>
                      <div className="flex flex-wrap gap-1">
                        {image.tags.map((tag) => (
                          <Badge key={tag} variant="outline" className="text-xs">
                            {tag}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  </>
                )}

                {/* Public URL */}
                {image.public && isDetailResponse(image) && image.public_url && (
                  <>
                    <Separator />
                    <div className="space-y-4">
                      <h4 className="text-sm font-medium">Public Access</h4>
                      <div className="text-xs font-mono bg-muted p-2 rounded break-all">
                        {image.public_url}
                      </div>
                    </div>
                  </>
                )}
              </div>
            </ScrollArea>

            {/* Footer Actions */}
            <div className="p-6 pt-4 border-t">
              <Button
                variant="destructive"
                size="sm"
                onClick={() => onDelete(image)}
                className="w-full"
              >
                <Trash2 className="mr-2 h-4 w-4" />
                Delete Image
              </Button>
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}