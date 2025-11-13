'use client'

import { useMemo } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import { 
  DollarSign, 
  TrendingUp, 
  AlertTriangle, 
  CheckCircle,
  Calendar,
  Zap,
  ArrowUpRight,
  Eye,
  Settings
} from 'lucide-react'
import { useVisionStore } from '@/lib/store/vision-store'

interface CostTrackerProps {
  className?: string
  compact?: boolean
  showDetails?: boolean
}

export function CostTracker({ 
  className, 
  compact = false,
  showDetails = true 
}: CostTrackerProps) {
  const { costMetrics, setShowCostTracker } = useVisionStore()
  
  const budgetUsagePercent = useMemo(() => {
    return Math.min((costMetrics.totalCost / costMetrics.monthlyBudget) * 100, 100)
  }, [costMetrics.totalCost, costMetrics.monthlyBudget])
  
  const dailyBudget = useMemo(() => {
    const daysInMonth = new Date(new Date().getFullYear(), new Date().getMonth() + 1, 0).getDate()
    return costMetrics.monthlyBudget / daysInMonth
  }, [costMetrics.monthlyBudget])
  
  const dailyUsagePercent = useMemo(() => {
    return Math.min((costMetrics.dailyUsage / dailyBudget) * 100, 100)
  }, [costMetrics.dailyUsage, dailyBudget])
  
  const getBudgetStatus = (percent: number) => {
    if (percent >= 90) return { color: 'red', icon: AlertTriangle, label: 'Critical' }
    if (percent >= 70) return { color: 'yellow', icon: ArrowUpRight, label: 'Warning' }
    return { color: 'green', icon: CheckCircle, label: 'Good' }
  }
  
  const monthlyStatus = getBudgetStatus(budgetUsagePercent)
  const dailyStatus = getBudgetStatus(dailyUsagePercent)
  
  const formatCurrency = (amount: number) => {
    return amount < 0.001 ? '<$0.001' : `$${amount.toFixed(3)}`
  }
  
  if (compact) {
    return (
      <div className={cn('flex items-center gap-2 text-sm', className)}>
        <DollarSign className="w-4 h-4 text-muted-foreground" />
        <span className="text-muted-foreground">Today:</span>
        <span className="font-medium">{formatCurrency(costMetrics.dailyUsage)}</span>
        <span className="text-muted-foreground">•</span>
        <span className="text-muted-foreground">Month:</span>
        <span className="font-medium">{formatCurrency(costMetrics.totalCost)}</span>
        <Badge 
          variant={monthlyStatus.color === 'green' ? 'default' : 'destructive'} 
          className="text-xs"
        >
          {budgetUsagePercent.toFixed(0)}%
        </Badge>
      </div>
    )
  }
  
  return (
    <Card className={cn('', className)}>
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center justify-between text-base">
          <div className="flex items-center gap-2">
            <DollarSign className="w-4 h-4" />
            Cost Tracker
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setShowCostTracker(false)}
            className="h-auto p-1"
          >
            <Eye className="w-4 h-4" />
          </Button>
        </CardTitle>
      </CardHeader>
      
      <CardContent className="space-y-4">
        {/* Monthly Budget Progress */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Calendar className="w-4 h-4 text-muted-foreground" />
              <span className="text-sm font-medium">Monthly Budget</span>
            </div>
            <div className="flex items-center gap-2">
              <monthlyStatus.icon className={cn('w-4 h-4', {
                'text-red-500': monthlyStatus.color === 'red',
                'text-yellow-500': monthlyStatus.color === 'yellow',
                'text-green-500': monthlyStatus.color === 'green',
              })} />
              <Badge variant={monthlyStatus.color === 'green' ? 'default' : 'destructive'} className="text-xs">
                {monthlyStatus.label}
              </Badge>
            </div>
          </div>
          
          <Progress 
            value={budgetUsagePercent} 
            className={cn('h-2', {
              '[&>div]:bg-red-500': monthlyStatus.color === 'red',
              '[&>div]:bg-yellow-500': monthlyStatus.color === 'yellow',
              '[&>div]:bg-green-500': monthlyStatus.color === 'green',
            })}
          />
          
          <div className="flex justify-between text-xs text-muted-foreground">
            <span>{formatCurrency(costMetrics.totalCost)} used</span>
            <span>{formatCurrency(costMetrics.monthlyBudget)} budget</span>
          </div>
        </div>
        
        {/* Daily Usage */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-muted-foreground" />
              <span className="text-sm font-medium">Today&apos;s Usage</span>
            </div>
            <Badge variant="outline" className="text-xs">
              {dailyUsagePercent.toFixed(0)}% of daily budget
            </Badge>
          </div>
          
          <Progress 
            value={dailyUsagePercent} 
            className={cn('h-2', {
              '[&>div]:bg-red-500': dailyStatus.color === 'red',
              '[&>div]:bg-yellow-500': dailyStatus.color === 'yellow',
              '[&>div]:bg-green-500': dailyStatus.color === 'green',
            })}
          />
          
          <div className="flex justify-between text-xs text-muted-foreground">
            <span>{formatCurrency(costMetrics.dailyUsage)} today</span>
            <span>{formatCurrency(dailyBudget)} daily target</span>
          </div>
        </div>
        
        {/* Model Usage Breakdown */}
        {showDetails && (costMetrics.gpt5Usage > 0 || costMetrics.fallbackUsage > 0) && (
          <div className="space-y-3 pt-3 border-t">
            <h4 className="text-sm font-medium flex items-center gap-2">
              <Zap className="w-4 h-4" />
              Model Usage Breakdown
            </h4>
            
            <div className="space-y-2">
              {/* GPT-5 Usage */}
              {costMetrics.gpt5Usage > 0 && (
                <div className="flex items-center justify-between text-sm">
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 bg-purple-500 rounded-full" />
                    <span>GPT-5 Vision</span>
                  </div>
                  <span className="font-medium">{formatCurrency(costMetrics.gpt5Usage)}</span>
                </div>
              )}
              
              {/* Fallback Model Usage */}
              {costMetrics.fallbackUsage > 0 && (
                <div className="flex items-center justify-between text-sm">
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 bg-blue-500 rounded-full" />
                    <span>Fallback Model</span>
                  </div>
                  <span className="font-medium">{formatCurrency(costMetrics.fallbackUsage)}</span>
                </div>
              )}
            </div>
            
            {/* Cost Distribution */}
            {costMetrics.gpt5Usage > 0 && costMetrics.fallbackUsage > 0 && (
              <div className="space-y-1">
                <div className="flex h-2 rounded-full overflow-hidden bg-muted">
                  <div
                    className="bg-purple-500 transition-all duration-300"
                    style={{
                      width: `${(costMetrics.gpt5Usage / costMetrics.totalCost) * 100}%`
                    }}
                  />
                  <div
                    className="bg-blue-500 transition-all duration-300"
                    style={{
                      width: `${(costMetrics.fallbackUsage / costMetrics.totalCost) * 100}%`
                    }}
                  />
                </div>
                <div className="text-xs text-muted-foreground text-center">
                  {((costMetrics.gpt5Usage / costMetrics.totalCost) * 100).toFixed(0)}% GPT-5 •
                  {' '}{((costMetrics.fallbackUsage / costMetrics.totalCost) * 100).toFixed(0)}% Fallback
                </div>
              </div>
            )}
          </div>
        )}
        
        {/* Budget Alerts */}
        {budgetUsagePercent >= 70 && (
          <div className={cn(
            'flex items-start gap-2 p-3 rounded-lg text-sm',
            budgetUsagePercent >= 90 
              ? 'bg-red-50 text-red-800 border border-red-200' 
              : 'bg-yellow-50 text-yellow-800 border border-yellow-200'
          )}>
            <AlertTriangle className="w-4 h-4 mt-0.5 flex-shrink-0" />
            <div>
              <p className="font-medium">
                {budgetUsagePercent >= 90 ? 'Budget Critical' : 'Budget Warning'}
              </p>
              <p className="text-xs mt-1">
                {budgetUsagePercent >= 90 
                  ? 'You have used 90%+ of your monthly budget. Consider upgrading or reducing usage.'
                  : 'You have used 70%+ of your monthly budget. Monitor usage closely.'
                }
              </p>
            </div>
          </div>
        )}
        
        {/* Settings Link */}
        <div className="pt-2 border-t">
          <Button variant="ghost" size="sm" className="w-full justify-start text-muted-foreground">
            <Settings className="w-4 h-4 mr-2" />
            Adjust Budget Settings
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}