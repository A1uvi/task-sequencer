import { Prompt, PromptVersion, PaginatedResponse, VisibilityType } from '../types'
import apiClient from './client'

export interface CreatePromptData {
  title: string
  folder_id?: string
  visibility_type: VisibilityType
}

export interface CreatePromptVersionData {
  content: string
  usage_notes?: string
  variables?: Record<string, unknown>
  example_input?: string
  example_output?: string
  meta_notes?: string
  tags?: string[]
}

export const promptsApi = {
  list: (folderId?: string, limit = 20, offset = 0): Promise<PaginatedResponse<Prompt>> => {
    const params: Record<string, unknown> = { limit, offset }
    if (folderId) params.folder_id = folderId
    return apiClient.get('/prompts', { params }).then((r) => r.data)
  },

  get: (id: string): Promise<Prompt> =>
    apiClient.get(`/prompts/${id}`).then((r) => r.data),

  create: (data: CreatePromptData): Promise<Prompt> =>
    apiClient.post('/prompts', data).then((r) => r.data),

  update: (id: string, data: Partial<Prompt>): Promise<Prompt> =>
    apiClient.patch(`/prompts/${id}`, data).then((r) => r.data),

  delete: (id: string): Promise<void> =>
    apiClient.delete(`/prompts/${id}`).then((r) => r.data),

  listVersions: (promptId: string): Promise<PromptVersion[]> =>
    apiClient.get(`/prompts/${promptId}/versions`).then((r) => r.data),

  getVersion: (promptId: string, versionId: string): Promise<PromptVersion> =>
    apiClient
      .get(`/prompts/${promptId}/versions/${versionId}`)
      .then((r) => r.data),

  createVersion: (
    promptId: string,
    data: CreatePromptVersionData
  ): Promise<PromptVersion> =>
    apiClient
      .post(`/prompts/${promptId}/versions`, data)
      .then((r) => r.data),
}
