'use client'

import { useState } from 'react'
import Image from 'next/image'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { 
  MoreHorizontal, 
  Eye, 
  Edit, 
  Trash2, 
  Download, 
  Copy, 
  ExternalLink,
  Calendar,
  FileText
} from 'lucide-react'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { ImageListResponse } from '@/lib/api/images'
import { imagesAPI } from '@/lib/api/images'

interface ImageCardProps {
  image: ImageListResponse
  onView: (image: ImageListResponse) => void
  onEdit: (image: ImageListResponse) => void
  onDelete: (image: ImageListResponse) => void
  className?: string
}

export function ImageCard({ image, onView, onEdit, onDelete, className = '' }: ImageCardProps) {
  const [imageLoading, setImageLoading] = useState(true)
  const [imageError, setImageError] = useState(false)

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
      month: 'short',
      day: 'numeric'
    })
  }

  return (
    <Card className={`group hover:shadow-lg transition-all duration-200 ${className}`}>
      <CardContent className="p-0">
        {/* Image Container */}
        <div className="relative aspect-square w-full overflow-hidden rounded-t-lg bg-muted">
          {!imageError ? (
            <Image
              src={image.url}
              alt={image.description || image.file_name}
              fill
              className={`object-cover transition-all duration-300 group-hover:scale-105 ${
                imageLoading ? 'blur-sm' : ''
              }`}
              onLoad={() => setImageLoading(false)}
              onError={() => {
                setImageError(true)
                setImageLoading(false)
              }}
              sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
            />
          ) : (
            <div className="flex h-full w-full items-center justify-center bg-muted">
              <FileText className="h-8 w-8 text-muted-foreground" />
            </div>
          )}
          
          {/* Loading Overlay */}
          {imageLoading && !imageError && (
            <div className="absolute inset-0 flex items-center justify-center bg-muted">
              <div className="h-6 w-6 animate-spin rounded-full border-2 border-primary border-t-transparent" />
            </div>
          )}

          {/* Action Buttons Overlay */}
          <div className="absolute inset-0 flex items-center justify-center bg-black/60 opacity-0 transition-opacity group-hover:opacity-100">
            <div className="flex gap-2">
              <Button
                size="sm"
                variant="secondary"
                onClick={() => onView(image)}
                className="h-8 w-8 p-0"
              >
                <Eye className="h-4 w-4" />
              </Button>
              <Button
                size="sm"
                variant="secondary"
                onClick={() => onEdit(image)}
                className="h-8 w-8 p-0"
              >
                <Edit className="h-4 w-4" />
              </Button>
            </div>
          </div>

          {/* Public Badge */}
          {image.public && (
            <div className="absolute top-2 left-2">
              <Badge variant="secondary" className="text-xs">
                <ExternalLink className="mr-1 h-3 w-3" />
                Public
              </Badge>
            </div>
          )}

          {/* Actions Menu */}
          <div className="absolute top-2 right-2">
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button 
                  size="sm" 
                  variant="secondary" 
                  className="h-8 w-8 p-0 opacity-0 group-hover:opacity-100 transition-opacity"
                >
                  <MoreHorizontal className="h-4 w-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem onClick={() => onView(image)}>
                  <Eye className="mr-2 h-4 w-4" />
                  View
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => onEdit(image)}>
                  <Edit className="mr-2 h-4 w-4" />
                  Edit
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={handleCopyUrl}>
                  <Copy className="mr-2 h-4 w-4" />
                  Copy URL
                </DropdownMenuItem>
                <DropdownMenuItem onClick={handleDownload}>
                  <Download className="mr-2 h-4 w-4" />
                  Download
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem 
                  onClick={() => onDelete(image)}
                  className="text-destructive focus:text-destructive"
                >
                  <Trash2 className="mr-2 h-4 w-4" />
                  Delete
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>

        {/* Image Info */}
        <div className="p-4">
          <div className="space-y-2">
            {/* Title */}
            <h3 className="font-medium truncate" title={image.file_name}>
              {image.file_name}
            </h3>
            
            {/* Description */}
            {image.description && (
              <p className="text-sm text-muted-foreground line-clamp-2" title={image.description}>
                {image.description}
              </p>
            )}

            {/* File Info */}
            <div className="flex items-center justify-between text-xs text-muted-foreground">
              <span>{imagesAPI.formatFileSize(image.file_size)}</span>
              <span className="flex items-center">
                <Calendar className="mr-1 h-3 w-3" />
                {formatDate(image.created_at)}
              </span>
            </div>

            {/* Tags */}
            {image.tags && image.tags.length > 0 && (
              <div className="flex flex-wrap gap-1">
                {image.tags.slice(0, 3).map((tag) => (
                  <Badge key={tag} variant="outline" className="text-xs">
                    {tag}
                  </Badge>
                ))}
                {image.tags.length > 3 && (
                  <Badge variant="outline" className="text-xs">
                    +{image.tags.length - 3}
                  </Badge>
                )}
              </div>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}