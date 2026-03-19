import { Task, TaskVersion, PaginatedResponse, VisibilityType } from '../types'
import apiClient from './client'

export interface CreateTaskData {
  title: string
  folder_id?: string
  visibility_type: VisibilityType
}

export interface CreateTaskVersionData {
  ordered_prompt_version_ids: string[]
  default_model: string
  allow_model_override_per_step: boolean
}

export const tasksApi = {
  list: (folderId?: string, limit = 20, offset = 0): Promise<PaginatedResponse<Task>> => {
    const params: Record<string, unknown> = { limit, offset }
    if (folderId) params.folder_id = folderId
    return apiClient.get('/tasks', { params }).then((r) => r.data)
  },

  get: (id: string): Promise<Task> =>
    apiClient.get(`/tasks/${id}`).then((r) => r.data),

  create: (data: CreateTaskData): Promise<Task> =>
    apiClient.post('/tasks', data).then((r) => r.data),

  update: (id: string, data: Partial<Task>): Promise<Task> =>
    apiClient.patch(`/tasks/${id}`, data).then((r) => r.data),

  delete: (id: string): Promise<void> =>
    apiClient.delete(`/tasks/${id}`).then((r) => r.data),

  listVersions: (taskId: string): Promise<TaskVersion[]> =>
    apiClient.get(`/tasks/${taskId}/versions`).then((r) => r.data),

  getVersion: (taskId: string, versionId: string): Promise<TaskVersion> =>
    apiClient
      .get(`/tasks/${taskId}/versions/${versionId}`)
      .then((r) => r.data),

  createVersion: (
    taskId: string,
    data: CreateTaskVersionData
  ): Promise<TaskVersion> =>
    apiClient
      .post(`/tasks/${taskId}/versions`, data)
      .then((r) => r.data),
}
