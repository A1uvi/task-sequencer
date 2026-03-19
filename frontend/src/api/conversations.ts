import { Conversation, PaginatedResponse } from '../types'
import apiClient from './client'

export const conversationsApi = {
  list: (limit = 20, offset = 0): Promise<PaginatedResponse<Conversation>> =>
    apiClient
      .get('/conversations', { params: { limit, offset } })
      .then((r) => r.data),

  get: (id: string): Promise<Conversation> =>
    apiClient.get(`/conversations/${id}`).then((r) => r.data),

  listByExecution: (executionId: string): Promise<Conversation[]> =>
    apiClient
      .get('/conversations', { params: { execution_id: executionId } })
      .then((r) => r.data),
}
