'use client'

import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import { agentConfigs, type Agent } from '@/types'

interface AgentIndicatorProps {
  agent: Agent
  className?: string
  showName?: boolean
  size?: 'sm' | 'md' | 'lg'
}

export function AgentIndicator({ 
  agent, 
  className, 
  showName = false,
  size = 'sm'
}: AgentIndicatorProps) {
  const config = agentConfigs[agent]
  
  if (!config || agent === 'user') {
    return null
  }

  const sizeClasses = {
    sm: 'text-xs px-2 py-0.5',
    md: 'text-sm px-2.5 py-1',
    lg: 'text-base px-3 py-1.5'
  }

  return (
    <Badge 
      variant="secondary" 
      className={cn(
        sizeClasses[size],
        `voxy-agent-${agent}`,
        'font-medium border border-current/20',
        className
      )}
    >
      <span className="mr-1">{config.icon}</span>
      {showName && config.name}
      {!showName && size !== 'sm' && config.name}
    </Badge>
  )
}