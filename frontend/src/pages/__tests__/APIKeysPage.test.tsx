import React from 'react'
import { render, screen, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router-dom'
import { vi } from 'vitest'
import { APIKeysPage } from '../APIKeysPage'

// Mock the hooks so the page doesn't try to hit a real API
vi.mock('../../hooks/useApiKeys', () => ({
  useApiKeys: vi.fn().mockReturnValue({
    data: [
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
    ],
    isLoading: false,
    error: null,
  }),
  useCreateApiKey: vi.fn().mockReturnValue({
    mutateAsync: vi.fn().mockResolvedValue({
      id: 'key-new',
      provider: 'openai',
      masked_key: '••••••••••••abcd',
      owner_type: 'user',
      owner_id: 'user-1',
      shared_with_users: [],
      shared_with_teams: [],
      status: 'active',
      created_at: new Date().toISOString(),
    }),
    isPending: false,
  }),
  useRevokeApiKey: vi.fn().mockReturnValue({
    mutateAsync: vi.fn().mockResolvedValue({
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
    isPending: false,
  }),
  useShareApiKey: vi.fn().mockReturnValue({
    mutateAsync: vi.fn().mockResolvedValue({}),
    isPending: false,
  }),
}))

function wrapper({ children }: { children: React.ReactNode }) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  return (
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>{children}</MemoryRouter>
    </QueryClientProvider>
  )
}

test('APIKeysPage renders without crashing', () => {
  render(<APIKeysPage />, { wrapper })
})

test('APIKeysPage renders heading', () => {
  render(<APIKeysPage />, { wrapper })
  expect(screen.getByRole('heading', { name: /api keys/i })).toBeInTheDocument()
})

test('APIKeysPage renders Add Key button', () => {
  render(<APIKeysPage />, { wrapper })
  expect(screen.getByRole('button', { name: /add key/i })).toBeInTheDocument()
})

test('APIKeysPage renders API keys table after loading', async () => {
  render(<APIKeysPage />, { wrapper })
  await waitFor(() => {
    // Table headers — use getAllByText since "Provider" appears in subtitle text too
    expect(screen.getAllByText(/Provider/i).length).toBeGreaterThan(0)
    expect(screen.getByText(/Status/i)).toBeInTheDocument()
  })
})

test('APIKeysPage renders masked keys from mock data', async () => {
  render(<APIKeysPage />, { wrapper })
  await waitFor(() => {
    expect(screen.getByText(/3a4f/)).toBeInTheDocument()
  })
})

test('APIKeysPage renders revoke buttons for active keys', async () => {
  render(<APIKeysPage />, { wrapper })
  await waitFor(() => {
    const revokeButtons = screen.getAllByText(/Revoke/i)
    expect(revokeButtons.length).toBeGreaterThan(0)
  })
})
