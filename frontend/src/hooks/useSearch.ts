import { useQuery } from '@tanstack/react-query'
import { searchApi, SearchParams } from '../api/search'

export function useSearch(params: SearchParams) {
  return useQuery({
    queryKey: ['search', params],
    queryFn: () => searchApi.search(params),
    enabled: !!params.q && params.q.trim().length > 0,
  })
}
