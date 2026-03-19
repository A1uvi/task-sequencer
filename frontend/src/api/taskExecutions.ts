import { TaskExecution, PaginatedResponse } from '../types'
import apiClient from './client'

export interface CreateTaskExecutionData {
  task_version_id: string
  api_key_id: string
}

export const taskExecutionsApi = {
  list: (limit = 20, offset = 0): Promise<PaginatedResponse<TaskExecution>> =>
    apiClient
      .get('/task-executions', { params: { limit, offset } })
      .then((r) => r.data),

  get: (id: string): Promise<TaskExecution> =>
    apiClient.get(`/task-executions/${id}`).then((r) => r.data),

  create: (data: CreateTaskExecutionData): Promise<TaskExecution> =>
    apiClient.post('/task-executions', data).then((r) => r.data),

  cancel: (id: string): Promise<TaskExecution> =>
    apiClient.patch(`/task-executions/${id}`, { status: 'failed' }).then((r) => r.data),

  listByTask: (taskVersionId: string): Promise<TaskExecution[]> =>
    apiClient
      .get('/task-executions', { params: { task_version_id: taskVersionId } })
      .then((r) => r.data),
}
