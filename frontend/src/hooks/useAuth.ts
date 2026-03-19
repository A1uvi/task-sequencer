import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { authApi, LoginRequest, RegisterRequest } from '../api/auth'

export function useCurrentUser() {
  return useQuery({
    queryKey: ['current-user'],
    queryFn: authApi.me,
    enabled: !!localStorage.getItem('access_token'),
    staleTime: 5 * 60 * 1000,
  })
}

export function useLogin() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: LoginRequest) => authApi.login(data.email, data.password),
    onSuccess: (tokens) => {
      localStorage.setItem('access_token', tokens.access_token)
      queryClient.invalidateQueries({ queryKey: ['current-user'] })
    },
  })
}

export function useRegister() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: RegisterRequest) => authApi.register(data.email, data.password),
    onSuccess: (tokens) => {
      localStorage.setItem('access_token', tokens.access_token)
      queryClient.invalidateQueries({ queryKey: ['current-user'] })
    },
  })
}

export function useUpdateNotificationPreferences() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (prefs: Record<string, boolean>) =>
      authApi.updateNotificationPreferences(prefs),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['current-user'] }),
  })
}

export function useLogout() {
  const queryClient = useQueryClient()
  return () => {
    localStorage.removeItem('access_token')
    queryClient.clear()
    window.location.href = '/login'
  }
}
