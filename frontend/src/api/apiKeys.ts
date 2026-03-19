import { APIKey, APIKeyOwnerType } from '../types'
import apiClient from './client'

export interface CreateAPIKeyData {
  provider: string
  key: string
  owner_type: APIKeyOwnerType
  owner_id: string
}

export interface ShareAPIKeyData {
  user_ids?: string[]
  team_ids?: string[]
}

export const apiKeysApi = {
  list: (): Promise<APIKey[]> =>
    apiClient.get('/api-keys').then((r) => r.data),

  get: (id: string): Promise<APIKey> =>
    apiClient.get(`/api-keys/${id}`).then((r) => r.data),

  // The backend encrypts the key server-side; we send provider + raw key only.
  create: (data: CreateAPIKeyData): Promise<APIKey> =>
    apiClient
      .post('/api-keys', { provider: data.provider, key: data.key })
      .then((r) => r.data),

  revoke: (id: string): Promise<APIKey> =>
    apiClient.patch(`/api-keys/${id}`, { status: 'revoked' }).then((r) => r.data),

  share: (id: string, data: ShareAPIKeyData): Promise<APIKey> =>
    apiClient.post(`/api-keys/${id}/share`, data).then((r) => r.data),

  delete: (id: string): Promise<void> =>
    apiClient.delete(`/api-keys/${id}`).then((r) => r.data),
}
