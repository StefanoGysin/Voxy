'use client'

import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent } from '@/components/ui/card'
import { 
  Wifi, 
  WifiOff, 
  RefreshCw, 
  AlertCircle, 
  Globe,
  Zap
} from 'lucide-react'

interface ConnectionStatusEnhancedProps {
  mode: 'websocket' | 'rest' | 'disabled'
  connectionState: 'connecting' | 'connected' | 'disconnected' | 'reconnecting' | 'failed'
  isLoading: boolean
  lastError?: string | null
  canRetryWebSocket: boolean
  onRetryWebSocket: () => void
  onForceRestMode: () => void
  wsRetryCount: number
  maxRetries: number
}

export function ConnectionStatusEnhanced({
  mode,
  connectionState,
  isLoading,
  lastError,
  canRetryWebSocket,
  onRetryWebSocket,
  onForceRestMode,
  wsRetryCount,
  maxRetries
}: ConnectionStatusEnhancedProps) {
  const getStatusColor = () => {
    if (mode === 'disabled') return 'bg-gray-500'
    if (mode === 'websocket' && connectionState === 'connected') return 'bg-green-500'
    if (mode === 'rest') return 'bg-blue-500'
    if (connectionState === 'connecting' || connectionState === 'reconnecting') return 'bg-yellow-500'
    return 'bg-red-500'
  }

  const getStatusIcon = () => {
    if (mode === 'disabled') return <WifiOff className="w-4 h-4" />
    if (mode === 'websocket' && connectionState === 'connected') return <Wifi className="w-4 h-4" />
    if (mode === 'rest') return <Globe className="w-4 h-4" />
    if (connectionState === 'connecting' || connectionState === 'reconnecting') return <RefreshCw className="w-4 h-4 animate-spin" />
    return <AlertCircle className="w-4 h-4" />
  }

  const getStatusText = () => {
    if (mode === 'disabled') return 'Offline'
    if (mode === 'websocket' && connectionState === 'connected') return 'Real-time Connected'
    if (mode === 'rest') return 'REST Mode'
    if (connectionState === 'connecting') return 'Connecting...'
    if (connectionState === 'reconnecting') return 'Reconnecting...'
    if (connectionState === 'failed') return 'Connection Failed'
    return 'Disconnected'
  }

  const getModeDescription = () => {
    if (mode === 'websocket' && connectionState === 'connected') {
      return 'Real-time messaging with instant responses'
    }
    if (mode === 'rest') {
      return 'Standard HTTP messaging (fallback mode)'
    }
    return 'Attempting to establish connection...'
  }

  // Don't show status for successful WebSocket connections (less clutter)
  const shouldShowStatus = mode !== 'websocket' || connectionState !== 'connected' || lastError

  if (!shouldShowStatus && !lastError) {
    return (
      <div className="flex items-center gap-2 text-xs text-muted-foreground">
        <div className={`w-2 h-2 rounded-full ${getStatusColor()}`} />
        <span>Connected</span>
      </div>
    )
  }

  return (
    <Card className="mb-4 border-l-4 border-l-primary/20">
      <CardContent className="p-4">
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-start gap-3 flex-1">
            <div className={`w-3 h-3 rounded-full ${getStatusColor()} mt-0.5 flex-shrink-0`} />
            
            <div className="flex-1 space-y-2">
              <div className="flex items-center gap-2">
                {getStatusIcon()}
                <span className="font-medium text-sm">{getStatusText()}</span>
                
                {mode === 'rest' && (
                  <Badge variant="secondary" className="text-xs">
                    <Zap className="w-3 h-3 mr-1" />
                    Fallback
                  </Badge>
                )}
                
                {isLoading && (
                  <Badge variant="outline" className="text-xs">
                    Processing...
                  </Badge>
                )}
              </div>
              
              <p className="text-xs text-muted-foreground">
                {getModeDescription()}
              </p>
              
              {lastError && (
                <div className="flex items-center gap-2 text-xs text-red-600 dark:text-red-400">
                  <AlertCircle className="w-3 h-3" />
                  <span>{lastError}</span>
                </div>
              )}
              
              {mode === 'rest' && wsRetryCount > 0 && (
                <p className="text-xs text-muted-foreground">
                  WebSocket failed after {wsRetryCount} attempts (max: {maxRetries})
                </p>
              )}
            </div>
          </div>
          
          <div className="flex items-center gap-2">
            {canRetryWebSocket && (
              <Button
                variant="outline"
                size="sm"
                onClick={onRetryWebSocket}
                className="text-xs h-7"
              >
                <RefreshCw className="w-3 h-3 mr-1" />
                Retry WebSocket
              </Button>
            )}
            
            {mode === 'websocket' && connectionState !== 'connected' && (
              <Button
                variant="outline"
                size="sm"
                onClick={onForceRestMode}
                className="text-xs h-7"
              >
                <Globe className="w-3 h-3 mr-1" />
                Use REST
              </Button>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}