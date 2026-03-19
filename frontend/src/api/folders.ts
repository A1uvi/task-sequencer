import { Folder, VisibilityType } from '../types'
import apiClient from './client'

export interface CreateFolderData {
  name: string
  visibility_type: VisibilityType
  team_ids?: string[]
}

export const foldersApi = {
  list: (): Promise<Folder[]> =>
    apiClient.get('/folders').then((r) => r.data),

  get: (id: string): Promise<Folder> =>
    apiClient.get(`/folders/${id}`).then((r) => r.data),

  create: (data: CreateFolderData): Promise<Folder> =>
    apiClient.post('/folders', data).then((r) => r.data),

  update: (id: string, data: Partial<Folder>): Promise<Folder> =>
    apiClient.patch(`/folders/${id}`, data).then((r) => r.data),

  delete: (id: string): Promise<void> =>
    apiClient.delete(`/folders/${id}`).then((r) => r.data),
}
