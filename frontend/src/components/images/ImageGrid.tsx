'use client'

import { ImageListResponse } from '@/lib/api/images'
import { ImageCard } from './ImageCard'
import { Skeleton } from '@/components/ui/skeleton'

interface ImageGridProps {
  images: ImageListResponse[]
  loading?: boolean
  onView: (image: ImageListResponse) => void
  onEdit: (image: ImageListResponse) => void
  onDelete: (image: ImageListResponse) => void
  className?: string
}

export function ImageGrid({ 
  images, 
  loading = false, 
  onView, 
  onEdit, 
  onDelete, 
  className = '' 
}: ImageGridProps) {
  
  if (loading) {
    return (
      <div className={`grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 2xl:grid-cols-6 gap-4 ${className}`}>
        {Array.from({ length: 12 }).map((_, index) => (
          <div key={index} className="space-y-3">
            <Skeleton className="aspect-square w-full rounded-lg" />
            <div className="space-y-2 p-1">
              <Skeleton className="h-4 w-3/4" />
              <Skeleton className="h-3 w-1/2" />
              <div className="flex gap-1">
                <Skeleton className="h-5 w-12 rounded-full" />
                <Skeleton className="h-5 w-12 rounded-full" />
              </div>
            </div>
          </div>
        ))}
      </div>
    )
  }

  if (images.length === 0) {
    return (
      <div className={`flex flex-col items-center justify-center py-12 ${className}`}>
        <div className="text-center space-y-3">
          <div className="mx-auto h-12 w-12 rounded-full bg-muted flex items-center justify-center">
            <svg
              className="h-6 w-6 text-muted-foreground"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
              />
            </svg>
          </div>
          <div>
            <h3 className="text-lg font-medium text-foreground">No images found</h3>
            <p className="text-sm text-muted-foreground">
              Start by uploading your first image or adjust your search filters.
            </p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className={`grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 2xl:grid-cols-6 gap-4 ${className}`}>
      {images.map((image) => (
        <ImageCard
          key={image.id}
          image={image}
          onView={onView}
          onEdit={onEdit}
          onDelete={onDelete}
        />
      ))}
    </div>
  )
}