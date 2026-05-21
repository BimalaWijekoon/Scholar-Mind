import { useState } from 'react'
import { Search as SearchIcon, Filter, FileText, Network, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { searchService } from '@/services/api'

interface SearchResult {
  id: string
  title: string
  snippet: string
  score: number
  type: 'document' | 'entity'
  documentId?: string
}

export default function Search() {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<SearchResult[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [hasSearched, setHasSearched] = useState(false)

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!query.trim()) return
    
    setIsLoading(true)
    setHasSearched(true)
    
    try {
      const data = await searchService.search(query)
      setResults(data.results || [])
    } catch (error) {
      console.error('Search failed:', error)
      setResults([])
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Search</h1>
        <p className="text-muted-foreground mt-1">
          Search across all your documents and knowledge
        </p>
      </div>

      {/* Search Form */}
      <Card>
        <CardContent className="pt-6">
          <form onSubmit={handleSearch} className="flex gap-2">
            <div className="relative flex-1">
              <SearchIcon className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                type="search"
                placeholder="Search documents, concepts, entities..."
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                className="pl-9"
              />
            </div>
            <Button type="submit" disabled={isLoading}>
              {isLoading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                'Search'
              )}
            </Button>
            <Button type="button" variant="outline">
              <Filter className="h-4 w-4 mr-2" />
              Filters
            </Button>
          </form>
        </CardContent>
      </Card>

      {/* Results */}
      {hasSearched && (
        <Card>
          <CardHeader>
            <CardTitle>Results</CardTitle>
            <CardDescription>
              {results.length} results found for "{query}"
            </CardDescription>
          </CardHeader>
          <CardContent>
            {results.length > 0 ? (
              <div className="space-y-4">
                {results.map((result) => (
                  <div
                    key={result.id}
                    className="flex gap-4 p-4 rounded-lg border hover:bg-accent/50 transition-colors cursor-pointer"
                  >
                    {result.type === 'document' ? (
                      <FileText className="h-8 w-8 text-blue-500 flex-shrink-0" />
                    ) : (
                      <Network className="h-8 w-8 text-purple-500 flex-shrink-0" />
                    )}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <h3 className="font-medium truncate">{result.title}</h3>
                        <span className="text-xs bg-muted px-2 py-0.5 rounded-full">
                          {result.type}
                        </span>
                      </div>
                      <p className="text-sm text-muted-foreground mt-1 line-clamp-2">
                        {result.snippet}
                      </p>
                      <div className="flex items-center gap-4 mt-2">
                        <span className="text-xs text-muted-foreground">
                          Relevance: {(result.score * 100).toFixed(0)}%
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center py-12 text-center">
                <SearchIcon className="h-12 w-12 text-muted-foreground mb-4" />
                <h3 className="text-lg font-medium">No results found</h3>
                <p className="text-sm text-muted-foreground mt-1">
                  Try adjusting your search terms
                </p>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Search Tips */}
      {!hasSearched && (
        <Card>
          <CardHeader>
            <CardTitle>Search Tips</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2 text-sm text-muted-foreground">
              <li>• Use natural language to search for concepts</li>
              <li>• Put phrases in quotes for exact matching</li>
              <li>• Search for specific entity types like "protein p53"</li>
              <li>• Use filters to narrow down by document type or date</li>
            </ul>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
