'use client'

import { useState, useEffect, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { 
  Search, 
  Filter, 
  Grid3X3, 
  List,
  RefreshCw,
  AlertCircle,
  Plus,
  ArrowLeft,
  Image as ImageIcon
} from 'lucide-react'
import { ImageGrid } from '@/components/images/ImageGrid'
import { ImageUpload } from '@/components/images/ImageUpload'
import { ImageModal } from '@/components/images/ImageModal'
import { EditImageForm } from '@/components/images/EditImageForm'
import { 
  ImageListResponse, 
  ImageDetailResponse, 
  ImageUploadResponse 
} from '@/lib/api/images'
import { imagesAPI } from '@/lib/api/images'
import { useAuthStore } from '@/lib/store/auth-store'
import { AuthService } from '@/lib/auth/auth-service'

interface ImageManagerState {
  images: ImageListResponse[]
  loading: boolean
  error: string | null
  searchQuery: string
  selectedTags: string[]
  showPublicOnly: boolean
  viewMode: 'grid' | 'list'
  showUpload: boolean
  selectedImage: ImageListResponse | ImageDetailResponse | null
  showImageModal: boolean
  showEditModal: boolean
}

export default function ImageManagerPage() {
  const router = useRouter()
  const { user, isLoading, isAuthenticated } = useAuthStore()

  const [state, setState] = useState<ImageManagerState>({
    images: [],
    loading: true,
    error: null,
    searchQuery: '',
    selectedTags: [],
    showPublicOnly: false,
    viewMode: 'grid',
    showUpload: false,
    selectedImage: null,
    showImageModal: false,
    showEditModal: false
  })

  // Initialize authentication on mount
  useEffect(() => {
    // Initialize auth on mount
    AuthService.initializeAuth()
    
    // Setup auth monitoring with proper cleanup
    const cleanup = AuthService.setupAuthMonitoring()
    
    // Cleanup function to stop monitoring when component unmounts
    return () => {
      cleanup()
      AuthService.stopAuthMonitoring()
    }
  }, [])

  // Redirect if not authenticated (wait for loading to complete)
  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push('/auth/login')
      return
    }
  }, [isLoading, isAuthenticated, router])

  const loadImages = useCallback(async () => {
    setState(prev => ({ ...prev, loading: true, error: null }))

    try {
      const images = await imagesAPI.listImages({
        publicOnly: state.showPublicOnly,
        tags: state.selectedTags.length > 0 ? state.selectedTags : undefined,
        limit: 100, // Load more images for better UX
        offset: 0
      })

      setState(prev => ({ 
        ...prev, 
        images, 
        loading: false 
      }))
    } catch (error) {
      console.error('Failed to load images:', error)
      setState(prev => ({ 
        ...prev, 
        loading: false, 
        error: error instanceof Error ? error.message : 'Failed to load images' 
      }))
    }
  }, [state.showPublicOnly, state.selectedTags])

  // Load images on component mount and when filters change
  useEffect(() => {
    if (!isLoading && isAuthenticated && user) {
      loadImages()
    }
  }, [isLoading, isAuthenticated, user, loadImages])

  const handleRefresh = () => {
    loadImages()
  }

  const handleSearchChange = (value: string) => {
    setState(prev => ({ ...prev, searchQuery: value }))
  }

  const handleFilterToggle = () => {
    setState(prev => ({ 
      ...prev, 
      showPublicOnly: !prev.showPublicOnly 
    }))
  }

  const handleViewModeToggle = () => {
    setState(prev => ({ 
      ...prev, 
      viewMode: prev.viewMode === 'grid' ? 'list' : 'grid' 
    }))
  }

  const handleUploadSuccess = (response: ImageUploadResponse) => {
    // Add the new image to the list
    const newImage: ImageListResponse = {
      id: response.id,
      file_name: response.file_name,
      file_size: response.file_size,
      content_type: response.content_type,
      description: response.description,
      tags: response.tags,
      public: response.public,
      url: response.url,
      created_at: response.created_at,
      updated_at: response.created_at
    }

    setState(prev => ({ 
      ...prev, 
      images: [newImage, ...prev.images],
      showUpload: false
    }))
  }

  const handleUploadError = (error: string) => {
    setState(prev => ({ ...prev, error }))
  }

  const handleImageView = async (image: ImageListResponse) => {
    try {
      // Get detailed image info
      const detailedImage = await imagesAPI.getImage(image.id)
      setState(prev => ({ 
        ...prev, 
        selectedImage: detailedImage,
        showImageModal: true 
      }))
    } catch (error) {
      console.error('Failed to load image details:', error)
      // Fallback to basic view
      setState(prev => ({ 
        ...prev, 
        selectedImage: image,
        showImageModal: true 
      }))
    }
  }

  const handleImageEdit = async (image: ImageListResponse | ImageDetailResponse) => {
    try {
      // Ensure we have detailed image info for editing
      if (!('storage_path' in image)) {
        const detailedImage = await imagesAPI.getImage(image.id)
        setState(prev => ({ 
          ...prev, 
          selectedImage: detailedImage,
          showEditModal: true,
          showImageModal: false
        }))
      } else {
        setState(prev => ({ 
          ...prev, 
          selectedImage: image,
          showEditModal: true,
          showImageModal: false
        }))
      }
    } catch (error) {
      console.error('Failed to load image details for editing:', error)
      setState(prev => ({ ...prev, error: 'Failed to load image details' }))
    }
  }

  const handleImageDelete = async (image: ImageListResponse | ImageDetailResponse) => {
    if (!confirm('Are you sure you want to delete this image? This action cannot be undone.')) {
      return
    }

    try {
      await imagesAPI.deleteImage(image.id)
      
      // Remove from list
      setState(prev => ({
        ...prev,
        images: prev.images.filter(img => img.id !== image.id),
        selectedImage: null,
        showImageModal: false,
        showEditModal: false
      }))
    } catch (error) {
      console.error('Failed to delete image:', error)
      setState(prev => ({ 
        ...prev, 
        error: error instanceof Error ? error.message : 'Failed to delete image'
      }))
    }
  }

  const handleEditSuccess = (updatedImage: ImageDetailResponse) => {
    // Update the image in the list
    const listImage: ImageListResponse = {
      id: updatedImage.id,
      file_name: updatedImage.file_name,
      file_size: updatedImage.file_size,
      content_type: updatedImage.content_type,
      description: updatedImage.description,
      tags: updatedImage.tags,
      public: updatedImage.public,
      url: updatedImage.url,
      created_at: updatedImage.created_at,
      updated_at: updatedImage.updated_at
    }

    setState(prev => ({
      ...prev,
      images: prev.images.map(img => 
        img.id === updatedImage.id ? listImage : img
      ),
      selectedImage: updatedImage,
      showEditModal: false
    }))
  }

  const handleEditError = (error: string) => {
    setState(prev => ({ ...prev, error }))
  }

  // Filter images based on search query
  const filteredImages = state.images.filter(image => {
    const matchesSearch = state.searchQuery === '' || 
      image.file_name.toLowerCase().includes(state.searchQuery.toLowerCase()) ||
      (image.description?.toLowerCase().includes(state.searchQuery.toLowerCase())) ||
      (image.tags?.some(tag => tag.toLowerCase().includes(state.searchQuery.toLowerCase())))

    return matchesSearch
  })

  // Get unique tags from all images for filter suggestions
  const allTags = Array.from(new Set(
    state.images.flatMap(image => image.tags || [])
  )).sort()

  // Show loading during authentication initialization
  if (isLoading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center space-y-4">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent mx-auto" />
          <p className="text-sm text-muted-foreground">Initializing authentication...</p>
        </div>
      </div>
    )
  }

  // Redirect will happen via useEffect if not authenticated
  if (!isAuthenticated || !user) {
    return null
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <div className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            {/* Title & Navigation */}
            <div className="flex items-center gap-4">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => router.push('/')}
                className="p-2"
              >
                <ArrowLeft className="h-4 w-4" />
              </Button>
              <div>
                <h1 className="text-2xl font-bold flex items-center gap-2">
                  <ImageIcon className="h-6 w-6" />
                  Image Manager
                </h1>
                <p className="text-sm text-muted-foreground">
                  Manage your uploaded images
                </p>
              </div>
            </div>

            {/* Actions */}
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={handleRefresh}
                disabled={state.loading}
              >
                <RefreshCw className={`h-4 w-4 ${state.loading ? 'animate-spin' : ''}`} />
              </Button>
              <Button
                size="sm"
                onClick={() => setState(prev => ({ ...prev, showUpload: !prev.showUpload }))}
              >
                <Plus className="h-4 w-4 mr-2" />
                Upload
              </Button>
            </div>
          </div>

          {/* Search and Filters */}
          <div className="flex flex-col sm:flex-row gap-4 mt-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search images by name, description, or tags..."
                value={state.searchQuery}
                onChange={(e) => handleSearchChange(e.target.value)}
                className="pl-10"
              />
            </div>
            
            <div className="flex gap-2">
              <Button
                variant={state.showPublicOnly ? "default" : "outline"}
                size="sm"
                onClick={handleFilterToggle}
              >
                <Filter className="h-4 w-4 mr-2" />
                {state.showPublicOnly ? 'Public Only' : 'All Images'}
              </Button>
              
              <Button
                variant="outline"
                size="sm"
                onClick={handleViewModeToggle}
              >
                {state.viewMode === 'grid' ? (
                  <List className="h-4 w-4" />
                ) : (
                  <Grid3X3 className="h-4 w-4" />
                )}
              </Button>
            </div>
          </div>

          {/* Results Info */}
          <div className="flex items-center justify-between mt-4 text-sm text-muted-foreground">
            <span>
              {filteredImages.length} of {state.images.length} images
              {state.searchQuery && ` matching "${state.searchQuery}"`}
            </span>
            {allTags.length > 0 && (
              <div className="flex items-center gap-1">
                <span>Tags:</span>
                {allTags.slice(0, 5).map(tag => (
                  <Badge key={tag} variant="outline" className="text-xs">
                    {tag}
                  </Badge>
                ))}
                {allTags.length > 5 && (
                  <Badge variant="outline" className="text-xs">
                    +{allTags.length - 5}
                  </Badge>
                )}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="container mx-auto px-4 py-6">
        {/* Upload Section */}
        {state.showUpload && (
          <div className="mb-8">
            <ImageUpload
              onUploadSuccess={handleUploadSuccess}
              onUploadError={handleUploadError}
            />
          </div>
        )}

        {/* Error Alert */}
        {state.error && (
          <Alert variant="destructive" className="mb-6">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>{state.error}</AlertDescription>
          </Alert>
        )}

        {/* Images Grid */}
        <ImageGrid
          images={filteredImages}
          loading={state.loading}
          onView={handleImageView}
          onEdit={handleImageEdit}
          onDelete={handleImageDelete}
        />
      </div>

      {/* Modals */}
      <ImageModal
        image={state.selectedImage}
        open={state.showImageModal}
        onClose={() => setState(prev => ({ 
          ...prev, 
          showImageModal: false, 
          selectedImage: null 
        }))}
        onEdit={handleImageEdit}
        onDelete={handleImageDelete}
      />

      <EditImageForm
        image={state.selectedImage}
        open={state.showEditModal}
        onClose={() => setState(prev => ({ 
          ...prev, 
          showEditModal: false, 
          selectedImage: null 
        }))}
        onSuccess={handleEditSuccess}
        onError={handleEditError}
      />
    </div>
  )
}