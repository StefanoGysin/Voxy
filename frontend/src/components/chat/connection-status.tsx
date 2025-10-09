'use client'

import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import { Wifi, WifiOff, Loader2, AlertCircle } from 'lucide-react'
import type { ConnectionState } from '@/types'

interface ConnectionStatusProps {
  status: ConnectionState
  className?: string
  compact?: boolean
}

const statusConfig = {
  connected: {
    icon: Wifi,
    label: 'Connected',
    variant: 'default' as const,
    className: 'voxy-status-connected'
  },
  connecting: {
    icon: Loader2,
    label: 'Connecting',
    variant: 'secondary' as const,
    className: 'voxy-status-connecting'
  },
  reconnecting: {
    icon: Loader2,
    label: 'Reconnecting',
    variant: 'secondary' as const,
    className: 'voxy-status-connecting'
  },
  disconnected: {
    icon: WifiOff,
    label: 'Disconnected',
    variant: 'destructive' as const,
    className: 'voxy-status-disconnected'
  },
  failed: {
    icon: AlertCircle,
    label: 'Connection Failed',
    variant: 'destructive' as const,
    className: 'voxy-status-disconnected'
  }
}

export function ConnectionStatus({ status, className, compact = false }: ConnectionStatusProps) {
  const config = statusConfig[status]
  const Icon = config.icon

  if (status === 'connected' && compact) {
    return null // Hide when connected in compact mode
  }

  return (
    <div className={cn('flex items-center justify-center p-2 border-b', className)}>
      <Badge variant={config.variant} className={cn('gap-2', config.className)}>
        <Icon 
          className={cn(
            'h-3 w-3',
            (status === 'connecting' || status === 'reconnecting') && 'animate-spin'
          )} 
        />
        <span className="text-xs font-medium">{config.label}</span>
      </Badge>
    </div>
  )
}