import { useQuery } from '@tanstack/react-query'
import { conversationsApi } from '../api/conversations'

export function useConversations() {
  return useQuery({
    queryKey: ['conversations'],
    queryFn: () => conversationsApi.list(),
  })
}

export function useConversation(id: string) {
  return useQuery({
    queryKey: ['conversations', id],
    queryFn: () => conversationsApi.get(id),
    enabled: !!id,
  })
}

export function useConversationsByExecution(executionId: string) {
  return useQuery({
    queryKey: ['conversations', 'by-execution', executionId],
    queryFn: () => conversationsApi.listByExecution(executionId),
    enabled: !!executionId,
  })
}
