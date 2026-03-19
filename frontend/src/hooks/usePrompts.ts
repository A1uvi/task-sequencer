import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { promptsApi, CreatePromptData, CreatePromptVersionData } from '../api/prompts'
import { Prompt } from '../types'

export function usePrompts(folderId?: string) {
  return useQuery({
    queryKey: ['prompts', folderId],
    queryFn: () => promptsApi.list(folderId),
  })
}

export function usePrompt(id: string) {
  return useQuery({
    queryKey: ['prompts', id],
    queryFn: () => promptsApi.get(id),
    enabled: !!id,
  })
}

export function useCreatePrompt() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: CreatePromptData) => promptsApi.create(data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['prompts'] }),
  })
}

export function useUpdatePrompt() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<Prompt> }) =>
      promptsApi.update(id, data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['prompts'] }),
  })
}

export function useDeletePrompt() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: promptsApi.delete,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['prompts'] }),
  })
}

export function usePromptVersions(promptId: string) {
  return useQuery({
    queryKey: ['prompt-versions', promptId],
    queryFn: () => promptsApi.listVersions(promptId),
    enabled: !!promptId,
  })
}

export function usePromptVersion(promptId: string, versionId: string) {
  return useQuery({
    queryKey: ['prompt-versions', promptId, versionId],
    queryFn: () => promptsApi.getVersion(promptId, versionId),
    enabled: !!promptId && !!versionId,
  })
}

export function useCreatePromptVersion() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({
      promptId,
      data,
    }: {
      promptId: string
      data: CreatePromptVersionData
    }) => promptsApi.createVersion(promptId, data),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({
        queryKey: ['prompt-versions', variables.promptId],
      })
      queryClient.invalidateQueries({ queryKey: ['prompts'] })
    },
  })
}
