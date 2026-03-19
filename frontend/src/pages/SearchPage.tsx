import React, { useEffect, useState } from 'react'
import { useSearchParams, Link } from 'react-router-dom'
import { useSearch } from '../hooks/useSearch'
import { LoadingSpinner } from '../components/common/LoadingSpinner'
import { EmptyState } from '../components/common/EmptyState'

type FilterType = 'all' | 'prompt' | 'task' | 'conversation'

const TYPE_COLORS: Record<string, string> = {
  prompt: 'bg-blue-100 text-blue-700',
  task: 'bg-purple-100 text-purple-700',
  conversation: 'bg-green-100 text-green-700',
}

const TYPE_HREFS: Record<string, (id: string) => string> = {
  prompt: (id) => `/prompts/${id}`,
  task: (id) => `/tasks/${id}`,
  conversation: (id) => `/conversations/${id}`,
}

export function SearchPage() {
  const [searchParams, setSearchParams] = useSearchParams()

  const [query, setQuery] = useState(searchParams.get('q') ?? '')
  const [filterType, setFilterType] = useState<FilterType>('all')

  const { data: results, isLoading } = useSearch({
    q: searchParams.get('q') ?? '',
    type: filterType === 'all' ? undefined : filterType,
  })

  useEffect(() => {
    document.title = 'Search — AI Workflow'
  }, [])

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    setSearchParams(query ? { q: query } : {})
  }

  const currentQuery = searchParams.get('q') ?? ''

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Search</h1>
        <p className="mt-1 text-sm text-gray-500">
          Search across all prompts, tasks, and conversations.
        </p>
      </div>

      {/* Search Bar */}
      <form onSubmit={handleSearch} className="flex gap-3">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search for prompts, tasks, conversations..."
          className="flex-1 rounded-md border border-gray-300 px-4 py-2.5 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          autoFocus
        />
        <button
          type="submit"
          className="rounded-md bg-blue-600 px-6 py-2.5 text-sm font-semibold text-white hover:bg-blue-500"
        >
          Search
        </button>
      </form>

      {/* Type Filter */}
      {currentQuery && (
        <div className="flex gap-2">
          {(['all', 'prompt', 'task', 'conversation'] as const).map((type) => (
            <button
              key={type}
              type="button"
              onClick={() => setFilterType(type)}
              className={`rounded-full px-4 py-1.5 text-sm font-medium capitalize transition-colors ${
                filterType === type
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              {type}
            </button>
          ))}
        </div>
      )}

      {/* Results */}
      {!currentQuery ? (
        <EmptyState
          title="Enter a search query"
          description="Type something above to search your prompts, tasks, and conversations."
        />
      ) : isLoading ? (
        <div className="flex justify-center py-12">
          <LoadingSpinner size="lg" />
        </div>
      ) : (results?.items.length ?? 0) === 0 ? (
        <EmptyState
          title="No results found"
          description={`No matches for "${currentQuery}". Try a different query or filter.`}
          action={{ label: 'Clear search', onClick: () => { setQuery(''); setSearchParams({}) } }}
        />
      ) : (
        <div className="space-y-3">
          <p className="text-sm text-gray-500">
            {results?.total ?? 0} result{(results?.total ?? 0) !== 1 ? 's' : ''} for &quot;{currentQuery}&quot;
          </p>
          <ul className="space-y-2">
            {results?.items.map((result) => (
              <li key={`${result.type}-${result.id}`}>
                <Link
                  to={TYPE_HREFS[result.type]?.(result.id) ?? '#'}
                  className="block rounded-xl bg-white p-4 shadow-sm ring-1 ring-gray-200 hover:shadow-md transition-shadow"
                >
                  <div className="flex items-center gap-2">
                    <span
                      className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-semibold capitalize ${
                        TYPE_COLORS[result.type] ?? 'bg-gray-100 text-gray-700'
                      }`}
                    >
                      {result.type}
                    </span>
                    <h3 className="text-sm font-semibold text-gray-900">
                      {result.title}
                    </h3>
                  </div>
                  <p className="mt-2 text-sm text-gray-600 line-clamp-2">
                    {result.snippet}
                  </p>
                  <p className="mt-2 text-xs text-gray-400">
                    {new Date(result.created_at).toLocaleDateString()}
                  </p>
                </Link>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
