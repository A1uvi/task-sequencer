import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { foldersApi, CreateFolderData } from '../api/folders'
import { Folder } from '../types'

export function useFolders() {
  return useQuery({
    queryKey: ['folders'],
    queryFn: foldersApi.list,
  })
}

export function useFolder(id: string) {
  return useQuery({
    queryKey: ['folders', id],
    queryFn: () => foldersApi.get(id),
    enabled: !!id,
  })
}

export function useCreateFolder() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: CreateFolderData) => foldersApi.create(data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['folders'] }),
  })
}

export function useUpdateFolder() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<Folder> }) =>
      foldersApi.update(id, data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['folders'] }),
  })
}

export function useDeleteFolder() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: foldersApi.delete,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['folders'] }),
  })
}
