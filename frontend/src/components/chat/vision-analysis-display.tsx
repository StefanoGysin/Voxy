'use client'

import { useState } from 'react'
import Image from 'next/image'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import { 
  Eye, 
  DollarSign, 
  Clock, 
  Zap, 
  Camera,
  Brain,
  Target
} from 'lucide-react'
import type { VisionAnalysis } from '@/types'

interface VisionAnalysisDisplayProps {
  analysis: VisionAnalysis
  className?: string
  compact?: boolean
}

export function VisionAnalysisDisplay({ 
  analysis, 
  className,
  compact = false 
}: VisionAnalysisDisplayProps) {
  const [imageLoaded, setImageLoaded] = useState(false)
  
  const formatCost = (cost: number) => {
    return cost < 0.001 ? '<$0.001' : `$${cost.toFixed(3)}`
  }
  
  const getModelBadgeVariant = (model: string) => {
    // Generic badge variant based on model name patterns
    if (model.toLowerCase().includes('gpt-5')) return 'default'
    if (model.toLowerCase().includes('gpt-4')) return 'secondary'
    return 'outline'
  }
  
  const getConfidenceColor = (confidence?: number) => {
    if (!confidence) return 'text-muted-foreground'
    if (confidence >= 0.8) return 'text-green-600'
    if (confidence >= 0.6) return 'text-yellow-600'
    return 'text-red-600'
  }
  
  
  if (compact) {
    return (
      <div className={cn('space-y-2', className)}>
        {/* Compact Image and Metadata */}
        <div className="flex gap-3">
          <div className="relative w-16 h-16 rounded-lg overflow-hidden flex-shrink-0">
            <Image 
              src={analysis.imageUrl}
              alt="Analysis"
              fill
              className={cn(
                'w-full h-full object-cover transition-opacity',
                imageLoaded ? 'opacity-100' : 'opacity-0'
              )}
              onLoad={() => setImageLoaded(true)}
            />
            {!imageLoaded && (
              <div className="absolute inset-0 bg-muted animate-pulse flex items-center justify-center">
                <Camera className="w-4 h-4 text-muted-foreground" />
              </div>
            )}
          </div>
          
          <div className="flex-1 space-y-1">
            <div className="flex items-center gap-2">
              <Badge variant={getModelBadgeVariant(analysis.modelUsed)} className="text-xs">
                {analysis.modelUsed.toUpperCase()}
              </Badge>
              <span className="text-xs text-muted-foreground">
                {analysis.processingTime.toFixed(1)}s
              </span>
              <span className="text-xs text-muted-foreground">
                {formatCost(analysis.cost)}
              </span>
            </div>
            
            {analysis.confidence && (
              <div className="flex items-center gap-1">
                <Target className="w-3 h-3 text-muted-foreground" />
                <span className={cn('text-xs font-medium', getConfidenceColor(analysis.confidence))}>
                  {Math.round(analysis.confidence * 100)}% confidence
                </span>
              </div>
            )}
          </div>
        </div>
        
        {/* Compact Analysis Text */}
        <div className="text-sm text-foreground bg-muted/30 rounded-lg p-3">
          <p className="line-clamp-3">{analysis.analysis}</p>
        </div>
      </div>
    )
  }
  
  return (
    <Card className={cn('overflow-hidden', className)}>
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center justify-between text-base">
          <div className="flex items-center gap-2">
            <Brain className="w-4 h-4" />
            Vision Analysis
          </div>
          <div className="flex items-center gap-2">
            <Badge variant={getModelBadgeVariant(analysis.modelUsed)}>
              ✨ {analysis.modelUsed}
            </Badge>
          </div>
        </CardTitle>
      </CardHeader>
      
      <CardContent className="space-y-4">
        {/* Image Display */}
        <div className="relative rounded-lg overflow-hidden bg-muted">
          <Image 
            src={analysis.imageUrl}
            alt="Analyzed image"
            fill
            className={cn(
              'object-cover transition-opacity',
              imageLoaded ? 'opacity-100' : 'opacity-0'
            )}
            onLoad={() => setImageLoaded(true)}
          />
          {!imageLoaded && (
            <div className="absolute inset-0 bg-muted animate-pulse flex items-center justify-center">
              <Camera className="w-8 h-8 text-muted-foreground" />
            </div>
          )}
          
          {/* Overlay with analysis type */}
          <div className="absolute top-2 left-2">
            <Badge variant="secondary" className="text-xs">
              <Eye className="w-3 h-3 mr-1" />
              {analysis.analysisType}
            </Badge>
          </div>
        </div>
        
        {/* Analysis Text */}
        <div className="space-y-2">
          <h4 className="text-sm font-medium flex items-center gap-2">
            <Zap className="w-4 h-4" />
            Analysis Results
          </h4>
          <div className="text-sm text-foreground bg-muted/30 rounded-lg p-3">
            <p className="whitespace-pre-wrap">{analysis.analysis}</p>
          </div>
        </div>
        
        {/* Metadata Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 pt-3 border-t">
          {/* Processing Time */}
          <div className="flex flex-col items-center space-y-1">
            <Clock className="w-4 h-4 text-muted-foreground" />
            <span className="text-xs text-muted-foreground">Processing</span>
            <span className="text-sm font-medium">{analysis.processingTime.toFixed(1)}s</span>
          </div>
          
          {/* Cost */}
          <div className="flex flex-col items-center space-y-1">
            <DollarSign className="w-4 h-4 text-muted-foreground" />
            <span className="text-xs text-muted-foreground">Cost</span>
            <span className="text-sm font-medium">{formatCost(analysis.cost)}</span>
          </div>
          
          {/* Confidence */}
          {analysis.confidence && (
            <div className="flex flex-col items-center space-y-1">
              <Target className={cn('w-4 h-4', getConfidenceColor(analysis.confidence))} />
              <span className="text-xs text-muted-foreground">Confidence</span>
              <span className={cn('text-sm font-medium', getConfidenceColor(analysis.confidence))}>
                {Math.round(analysis.confidence * 100)}%
              </span>
            </div>
          )}
          
          {/* Model */}
          <div className="flex flex-col items-center space-y-1">
            <Brain className="w-4 h-4 text-muted-foreground" />
            <span className="text-xs text-muted-foreground">Model</span>
            <Badge variant={getModelBadgeVariant(analysis.modelUsed)} className="text-xs">
              {analysis.modelUsed.toUpperCase()}
            </Badge>
          </div>
        </div>
        
        {/* Timestamp */}
        <div className="text-xs text-muted-foreground text-center pt-2 border-t">
          Analyzed on {analysis.timestamp.toLocaleString()}
        </div>
      </CardContent>
    </Card>
  )
}