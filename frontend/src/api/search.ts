import { SearchResult, PaginatedResponse } from '../types'
import apiClient from './client'

export interface SearchParams {
  q: string
  type?: 'prompt' | 'task' | 'conversation' | 'all'
  limit?: number
  offset?: number
}

export const searchApi = {
  search: (params: SearchParams): Promise<PaginatedResponse<SearchResult>> => {
    const queryParams: Record<string, unknown> = {
      q: params.q,
      limit: params.limit ?? 20,
      offset: params.offset ?? 0,
    }
    if (params.type && params.type !== 'all') {
      queryParams.type = params.type
    }
    return apiClient.get('/search', { params: queryParams }).then((r) => r.data)
  },
}
