import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { taskExecutionsApi, CreateTaskExecutionData } from '../api/taskExecutions'
import { TaskExecution, TaskExecutionStatus, PaginatedResponse } from '../types'

const TERMINAL_STATUSES: TaskExecutionStatus[] = [
  'completed',
  'failed',
  'paused_exhausted',
]

export function useTaskExecutions() {
  return useQuery<PaginatedResponse<TaskExecution>>({
    queryKey: ['task-executions'],
    queryFn: () => taskExecutionsApi.list(),
  })
}

export function useTaskExecution(id: string) {
  return useQuery({
    queryKey: ['task-executions', id],
    queryFn: () => taskExecutionsApi.get(id),
    enabled: !!id,
    refetchInterval: (query) => {
      const status = query.state.data?.status
      if (!status) return false
      return TERMINAL_STATUSES.includes(status) ? false : 3000
    },
  })
}

export function useCreateTaskExecution() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: CreateTaskExecutionData) =>
      taskExecutionsApi.create(data),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: ['task-executions'] }),
  })
}

export function useCancelTaskExecution() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: taskExecutionsApi.cancel,
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: ['task-executions'] }),
  })
}

export function useTaskExecutionsByTask(taskVersionId: string) {
  return useQuery({
    queryKey: ['task-executions', 'by-task', taskVersionId],
    queryFn: () => taskExecutionsApi.listByTask(taskVersionId),
    enabled: !!taskVersionId,
  })
}
