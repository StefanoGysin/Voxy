'use client'

import { useState } from 'react'
import { Search, Filter, User, Bot, X, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Label } from '@/components/ui/label'
import { useMessageSearch, type MessageSearchFilters, type MessageSearchResult } from '@/lib/hooks/use-message-search'

interface AdvancedSearchProps {
  onResultSelect?: (result: MessageSearchResult) => void
}

export function AdvancedSearch({ onResultSelect }: AdvancedSearchProps) {
  const [searchQuery, setSearchQuery] = useState('')
  const [isFiltersOpen, setIsFiltersOpen] = useState(false)
  const [filters, setFilters] = useState<Partial<MessageSearchFilters>>({})
  
  const { 
    searchResults, 
    isSearching, 
    error, 
    totalResults,
    searchTime,
    lastSearchQuery,
    searchAllMessages,
    clearSearch 
  } = useMessageSearch()

  // const { sessions } = useSessionStore() // Removed unused sessions

  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      clearSearch()
      return
    }

    const searchFilters: MessageSearchFilters = {
      query: searchQuery.trim(),
      ...filters,
      limit: 50,
    }

    try {
      await searchAllMessages(searchFilters)
    } catch (error) {
      console.error('Search failed:', error)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSearch()
    }
  }

  const updateFilter = (key: keyof MessageSearchFilters, value: string | number | undefined) => {
    setFilters(prev => ({
      ...prev,
      [key]: value,
    }))
  }

  const clearAllFilters = () => {
    setFilters({})
    setSearchQuery('')
    clearSearch()
  }

  const hasActiveFilters = Object.keys(filters).some(key => {
    const value = filters[key as keyof MessageSearchFilters]
    return value !== undefined && value !== null && value !== ''
  })

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('pt-BR', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const getAgentColor = (agent?: string) => {
    switch (agent) {
      case 'voxy': return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300'
      case 'translator': return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300'
      case 'corrector': return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300'
      case 'weather': return 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-300'
      case 'calculator': return 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-300'
      default: return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-300'
    }
  }

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Search className="h-5 w-5" />
          Advanced Message Search
        </CardTitle>
        <CardDescription>
          Search across all your conversations with advanced filtering
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Search Input */}
        <div className="flex gap-2">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
            <Input
              type="text"
              placeholder="Search your messages..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyPress={handleKeyPress}
              className="pl-10"
            />
          </div>
          <Dialog open={isFiltersOpen} onOpenChange={setIsFiltersOpen}>
            <DialogTrigger asChild>
              <Button variant="outline" size="icon" className="relative">
                <Filter className="h-4 w-4" />
                {hasActiveFilters && (
                  <span className="absolute -top-1 -right-1 h-3 w-3 bg-blue-600 rounded-full" />
                )}
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Search Filters</DialogTitle>
                <DialogDescription>
                  Refine your search with these advanced options
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4">
                {/* Role Filter */}
                <div>
                  <Label htmlFor="role">Message Role</Label>
                  <select
                    id="role"
                    value={filters.roleFilter || ''}
                    onChange={(e) => updateFilter('roleFilter', e.target.value || undefined)}
                    className="w-full mt-1 p-2 border rounded-md bg-background"
                  >
                    <option value="">All Messages</option>
                    <option value="user">My Messages</option>
                    <option value="assistant">AI Responses</option>
                  </select>
                </div>

                {/* Agent Filter */}
                <div>
                  <Label htmlFor="agent">AI Agent</Label>
                  <select
                    id="agent"
                    value={filters.agentFilter || ''}
                    onChange={(e) => updateFilter('agentFilter', e.target.value || undefined)}
                    className="w-full mt-1 p-2 border rounded-md bg-background"
                  >
                    <option value="">All Agents</option>
                    <option value="voxy">VOXY</option>
                    <option value="translator">Translator</option>
                    <option value="corrector">Corrector</option>
                    <option value="weather">Weather</option>
                    <option value="calculator">Calculator</option>
                  </select>
                </div>

                {/* Date Range */}
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <Label htmlFor="dateFrom">From Date</Label>
                    <Input
                      type="date"
                      id="dateFrom"
                      value={filters.dateFrom || ''}
                      onChange={(e) => updateFilter('dateFrom', e.target.value || undefined)}
                    />
                  </div>
                  <div>
                    <Label htmlFor="dateTo">To Date</Label>
                    <Input
                      type="date"
                      id="dateTo"
                      value={filters.dateTo || ''}
                      onChange={(e) => updateFilter('dateTo', e.target.value || undefined)}
                    />
                  </div>
                </div>

                {/* Limit */}
                <div>
                  <Label htmlFor="limit">Max Results</Label>
                  <select
                    id="limit"
                    value={filters.limit || 50}
                    onChange={(e) => updateFilter('limit', parseInt(e.target.value))}
                    className="w-full mt-1 p-2 border rounded-md bg-background"
                  >
                    <option value={25}>25 results</option>
                    <option value={50}>50 results</option>
                    <option value={100}>100 results</option>
                    <option value={200}>200 results</option>
                  </select>
                </div>

                <Button onClick={() => setIsFiltersOpen(false)} className="w-full">
                  Apply Filters
                </Button>
              </div>
            </DialogContent>
          </Dialog>
          <Button onClick={handleSearch} disabled={isSearching}>
            {isSearching ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Search'}
          </Button>
          {(hasActiveFilters || searchQuery || searchResults.length > 0) && (
            <Button variant="outline" onClick={clearAllFilters}>
              <X className="h-4 w-4" />
            </Button>
          )}
        </div>

        {/* Active Filters Display */}
        {hasActiveFilters && (
          <div className="flex flex-wrap gap-2">
            {filters.roleFilter && (
              <Badge variant="secondary">
                Role: {filters.roleFilter === 'user' ? 'My Messages' : 'AI Responses'}
              </Badge>
            )}
            {filters.agentFilter && (
              <Badge variant="secondary">
                Agent: {filters.agentFilter.toUpperCase()}
              </Badge>
            )}
            {filters.dateFrom && (
              <Badge variant="secondary">
                From: {new Date(filters.dateFrom).toLocaleDateString('pt-BR')}
              </Badge>
            )}
            {filters.dateTo && (
              <Badge variant="secondary">
                Until: {new Date(filters.dateTo).toLocaleDateString('pt-BR')}
              </Badge>
            )}
          </div>
        )}

        {/* Search Results */}
        {error && (
          <div className="p-4 border border-red-200 bg-red-50 dark:bg-red-950/20 rounded-md">
            <p className="text-red-800 dark:text-red-200">{error}</p>
          </div>
        )}

        {isSearching && (
          <div className="space-y-2">
            <Skeleton className="h-20 w-full" />
            <Skeleton className="h-20 w-full" />
            <Skeleton className="h-20 w-full" />
          </div>
        )}

        {!isSearching && lastSearchQuery && (
          <div className="flex items-center justify-between text-sm text-muted-foreground">
            <span>
              {totalResults} result{totalResults !== 1 ? 's' : ''} for &quot;{lastSearchQuery}&quot;
            </span>
            {searchTime > 0 && (
              <span>
                Search completed in {searchTime.toFixed(0)}ms
              </span>
            )}
          </div>
        )}

        {!isSearching && searchResults.length > 0 && (
          <div className="space-y-3 max-h-96 overflow-y-auto">
            {searchResults.map((result) => (
              <div 
                key={result.id} 
                className="p-4 border rounded-lg hover:bg-muted/50 cursor-pointer transition-colors"
                onClick={() => onResultSelect?.(result)}
              >
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-center gap-2">
                    {result.role === 'user' ? (
                      <User className="h-4 w-4 text-blue-500" />
                    ) : (
                      <Bot className="h-4 w-4 text-purple-500" />
                    )}
                    <Badge className={getAgentColor(result.agent_type)}>
                      {result.agent_type?.toUpperCase() || 'VOXY'}
                    </Badge>
                    <span className="text-xs text-muted-foreground">
                      Score: {(result.relevance_score * 100).toFixed(0)}%
                    </span>
                  </div>
                  <div className="text-xs text-muted-foreground">
                    {formatDate(result.created_at)}
                  </div>
                </div>
                
                <div className="space-y-2">
                  <div 
                    className="text-sm"
                    dangerouslySetInnerHTML={{ __html: result.highlighted_content }}
                  />
                  
                  {result.session_title && (
                    <div className="text-xs text-muted-foreground">
                      Session: {result.session_title}
                    </div>
                  )}

                  {(result.context_before || result.context_after) && (
                    <div className="text-xs text-muted-foreground border-l-2 border-gray-200 pl-2">
                      {result.context_before && (
                        <div>← {result.context_before}</div>
                      )}
                      {result.context_after && (
                        <div>→ {result.context_after}</div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}

        {!isSearching && lastSearchQuery && searchResults.length === 0 && (
          <div className="text-center py-8 text-muted-foreground">
            <Search className="h-12 w-12 mx-auto mb-4 opacity-50" />
            <p>No messages found for &quot;{lastSearchQuery}&quot;</p>
            <p className="text-sm">Try different keywords or adjust your filters</p>
          </div>
        )}
      </CardContent>
    </Card>
  )
}