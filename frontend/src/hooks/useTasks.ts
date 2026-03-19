import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { tasksApi, CreateTaskData, CreateTaskVersionData } from '../api/tasks'
import { Task } from '../types'

export function useTasks(folderId?: string) {
  return useQuery({
    queryKey: ['tasks', folderId],
    queryFn: () => tasksApi.list(folderId),
  })
}

export function useTask(id: string) {
  return useQuery({
    queryKey: ['tasks', id],
    queryFn: () => tasksApi.get(id),
    enabled: !!id,
  })
}

export function useCreateTask() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: CreateTaskData) => tasksApi.create(data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['tasks'] }),
  })
}

export function useUpdateTask() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<Task> }) =>
      tasksApi.update(id, data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['tasks'] }),
  })
}

export function useDeleteTask() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: tasksApi.delete,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['tasks'] }),
  })
}

export function useTaskVersions(taskId: string) {
  return useQuery({
    queryKey: ['task-versions', taskId],
    queryFn: () => tasksApi.listVersions(taskId),
    enabled: !!taskId,
  })
}

export function useTaskVersion(taskId: string, versionId: string) {
  return useQuery({
    queryKey: ['task-versions', taskId, versionId],
    queryFn: () => tasksApi.getVersion(taskId, versionId),
    enabled: !!taskId && !!versionId,
  })
}

export function useCreateTaskVersion() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({
      taskId,
      data,
    }: {
      taskId: string
      data: CreateTaskVersionData
    }) => tasksApi.createVersion(taskId, data),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({
        queryKey: ['task-versions', variables.taskId],
      })
      queryClient.invalidateQueries({ queryKey: ['tasks'] })
    },
  })
}
