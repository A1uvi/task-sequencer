import React from 'react'
import { renderHook, waitFor, act } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { vi } from 'vitest'
import { useApiKeys, useCreateApiKey, useRevokeApiKey, useShareApiKey } from '../useApiKeys'

// Mock the API module so no real HTTP requests are made
vi.mock('../../api/apiKeys', () => ({
  apiKeysApi: {
    list: vi.fn().mockResolvedValue([
      {
        id: 'key-1',
        provider: 'openai',
        masked_key: '••••••••••••3a4f',
        owner_type: 'user',
        owner_id: 'user-1',
        shared_with_users: [],
        shared_with_teams: [],
        status: 'active',
        created_at: '2024-01-01T00:00:00Z',
      },
      {
        id: 'key-2',
        provider: 'anthropic',
        masked_key: '••••••••••••7b2c',
        owner_type: 'user',
        owner_id: 'user-1',
        shared_with_users: ['user-2'],
        shared_with_teams: ['team-1'],
        status: 'active',
        created_at: '2024-01-05T00:00:00Z',
      },
    ]),
    get: vi.fn(),
    create: vi.fn().mockImplementation((data) => {
      const maskedKey = `••••••••••••${data.key.slice(-4)}`
      return Promise.resolve({
        id: `key-${Date.now()}`,
        provider: data.provider,
        masked_key: maskedKey,
        owner_type: data.owner_type,
        owner_id: data.owner_id,
        shared_with_users: [],
        shared_with_teams: [],
        status: 'active',
        created_at: new Date().toISOString(),
      })
    }),
    revoke: vi.fn().mockResolvedValue({
      id: 'key-1',
      provider: 'openai',
      masked_key: '••••••••••••3a4f',
      owner_type: 'user',
      owner_id: 'user-1',
      shared_with_users: [],
      shared_with_teams: [],
      status: 'revoked',
      created_at: '2024-01-01T00:00:00Z',
    }),
    share: vi.fn().mockImplementation((_id, data) =>
      Promise.resolve({
        id: 'key-1',
        provider: 'openai',
        masked_key: '••••••••••••3a4f',
        owner_type: 'user',
        owner_id: 'user-1',
        shared_with_users: data.user_ids ?? [],
        shared_with_teams: data.team_ids ?? [],
        status: 'active',
        created_at: '2024-01-01T00:00:00Z',
      })
    ),
    delete: vi.fn().mockResolvedValue(undefined),
  },
}))

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })
  return ({ children }: { children: React.ReactNode }) =>
    React.createElement(QueryClientProvider, { client: queryClient }, children)
}

test('useApiKeys returns a list of API keys', async () => {
  const wrapper = createWrapper()
  const { result } = renderHook(() => useApiKeys(), { wrapper })
  await waitFor(() => expect(result.current.isSuccess).toBe(true))
  expect(Array.isArray(result.current.data)).toBe(true)
  expect(result.current.data?.length).toBeGreaterThan(0)
})

test('API keys have required fields', async () => {
  const wrapper = createWrapper()
  const { result } = renderHook(() => useApiKeys(), { wrapper })
  await waitFor(() => expect(result.current.isSuccess).toBe(true))
  const key = result.current.data?.[0]
  expect(key).toHaveProperty('id')
  expect(key).toHaveProperty('provider')
  expect(key).toHaveProperty('masked_key')
  expect(key).toHaveProperty('status')
})

test('useCreateApiKey creates a key and masks it', async () => {
  const wrapper = createWrapper()
  const { result } = renderHook(() => useCreateApiKey(), { wrapper })
  let data: unknown
  await act(async () => {
    data = await result.current.mutateAsync({
      provider: 'openai',
      key: 'sk-test1234567890abcd',
      owner_type: 'user',
      owner_id: 'user-1',
    })
  })
  await waitFor(() => expect(result.current.isSuccess).toBe(true))
  const key = data as { masked_key: string }
  // masked_key should only show last 4 chars
  expect(key.masked_key).toContain('abcd')
  // full key should not be exposed
  expect(key.masked_key).not.toBe('sk-test1234567890abcd')
})

test('useRevokeApiKey sets status to revoked', async () => {
  const wrapper = createWrapper()
  const { result } = renderHook(() => useRevokeApiKey(), { wrapper })
  let data: unknown
  await act(async () => {
    data = await result.current.mutateAsync('key-1')
  })
  await waitFor(() => expect(result.current.isSuccess).toBe(true))
  expect((data as { status: string }).status).toBe('revoked')
})

test('useShareApiKey updates shared_with_users', async () => {
  const wrapper = createWrapper()
  const { result } = renderHook(() => useShareApiKey(), { wrapper })
  let data: unknown
  await act(async () => {
    data = await result.current.mutateAsync({
      id: 'key-1',
      data: { user_ids: ['user-2', 'user-3'] },
    })
  })
  await waitFor(() => expect(result.current.isSuccess).toBe(true))
  expect((data as { shared_with_users: string[] }).shared_with_users).toContain('user-2')
})
