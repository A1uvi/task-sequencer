import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiKeysApi, CreateAPIKeyData, ShareAPIKeyData } from '../api/apiKeys'

export function useApiKeys() {
  return useQuery({
    queryKey: ['api-keys'],
    queryFn: apiKeysApi.list,
  })
}

export function useApiKey(id: string) {
  return useQuery({
    queryKey: ['api-keys', id],
    queryFn: () => apiKeysApi.get(id),
    enabled: !!id,
  })
}

export function useCreateApiKey() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: CreateAPIKeyData) => apiKeysApi.create(data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['api-keys'] }),
  })
}

export function useRevokeApiKey() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: apiKeysApi.revoke,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['api-keys'] }),
  })
}

export function useShareApiKey() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: ShareAPIKeyData }) =>
      apiKeysApi.share(id, data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['api-keys'] }),
  })
}

export function useDeleteApiKey() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: apiKeysApi.delete,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['api-keys'] }),
  })
}
