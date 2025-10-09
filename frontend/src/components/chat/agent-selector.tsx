'use client'

import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { cn } from '@/lib/utils'
import { useState } from 'react'

interface Agent {
  id: string
  name: string
  icon: string
  description: string
  color: string
  prompt: string
}

const agents: Agent[] = [
  {
    id: 'voxy',
    name: 'VOXY',
    icon: '🧠',
    description: 'Assistente de IA geral',
    color: 'blue',
    prompt: 'Pergunte-me qualquer coisa!'
  },
  {
    id: 'translator',
    name: 'Tradutor',
    icon: '🌍',
    description: 'Traduzir texto entre idiomas',
    color: 'green',
    prompt: 'O que você gostaria que eu traduzisse?'
  },
  {
    id: 'corrector',
    name: 'Corretor',
    icon: '✏️',
    description: 'Corrigir gramática e melhorar texto',
    color: 'purple',
    prompt: 'Compartilhe o texto que quer que eu corrija e melhore.'
  },
  {
    id: 'weather',
    name: 'Clima',
    icon: '🌤️',
    description: 'Obter informações meteorológicas',
    color: 'sky',
    prompt: 'Para qual localização você quer informações do clima?'
  },
  {
    id: 'calculator',
    name: 'Calculadora',
    icon: '🧮',
    description: 'Resolver problemas matemáticos',
    color: 'orange',
    prompt: 'Que cálculo você gostaria que eu fizesse?'
  }
]

interface AgentSelectorProps {
  onSelectAgent: (agent: Agent) => void
  selectedAgent?: string
  className?: string
}

export function AgentSelector({ onSelectAgent, selectedAgent, className }: AgentSelectorProps) {
  const [isExpanded, setIsExpanded] = useState(false)

  const currentAgent = agents.find(agent => agent.id === selectedAgent) || agents[0]

  const handleAgentSelect = (agent: Agent) => {
    onSelectAgent(agent)
    setIsExpanded(false)
  }

  if (!isExpanded) {
    return (
      <div className={cn('flex items-center gap-2', className)}>
        <Button
          variant="outline"
          size="sm"
          onClick={() => setIsExpanded(true)}
          className={cn(
            'flex items-center gap-2 h-8',
            selectedAgent && selectedAgent !== 'voxy' && `border-${currentAgent.color}-500 text-${currentAgent.color}-600`
          )}
        >
          <span className="text-sm">{currentAgent.icon}</span>
          <span className="text-xs font-medium">{currentAgent.name}</span>
        </Button>
        <span className="text-xs text-muted-foreground">
          {currentAgent.prompt}
        </span>
      </div>
    )
  }

  return (
    <Card className={cn('border-2', className)}>
      <CardContent className="p-3">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-semibold">Escolha seu Agente</h3>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setIsExpanded(false)}
            className="h-6 w-6 p-0"
          >
            ×
          </Button>
        </div>
        
        <div className="grid grid-cols-2 md:grid-cols-5 gap-2">
          {agents.map((agent) => {
            const isSelected = selectedAgent === agent.id
            
            return (
              <Button
                key={agent.id}
                variant={isSelected ? "default" : "outline"}
                size="sm"
                onClick={() => handleAgentSelect(agent)}
                className={cn(
                  'flex flex-col items-center gap-1 h-auto p-3 transition-all',
                  isSelected && `bg-${agent.color}-500 hover:bg-${agent.color}-600 text-white`,
                  !isSelected && `hover:border-${agent.color}-500 hover:text-${agent.color}-600`
                )}
              >
                <span className="text-lg">{agent.icon}</span>
                <span className="text-xs font-medium">{agent.name}</span>
              </Button>
            )
          })}
        </div>
        
        <div className="mt-3 p-2 bg-muted rounded-md">
          <p className="text-xs text-muted-foreground">
            <strong>{currentAgent.name}:</strong> {currentAgent.description}
          </p>
        </div>
      </CardContent>
    </Card>
  )
}