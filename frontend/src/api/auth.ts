import { AuthTokens, User } from '../types'
import apiClient from './client'

export interface LoginRequest {
  email: string
  password: string
}

export interface RegisterRequest {
  email: string
  password: string
}

export const authApi = {
  login: (email: string, password: string): Promise<AuthTokens> =>
    apiClient
      .post('/auth/login', new URLSearchParams({ username: email, password }), {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      })
      .then((r) => r.data),

  register: (email: string, password: string): Promise<AuthTokens> =>
    apiClient.post('/auth/register', { email, password }).then((r) => r.data),

  me: (): Promise<User> => apiClient.get('/auth/me').then((r) => r.data),

  updateNotificationPreferences: (
    prefs: Record<string, boolean>
  ): Promise<User> =>
    apiClient
      .patch('/auth/me/notification-preferences', prefs)
      .then((r) => r.data),
}
