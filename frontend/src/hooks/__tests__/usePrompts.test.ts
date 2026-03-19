import React from 'react'
import { renderHook, waitFor, act } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { vi } from 'vitest'
import { usePrompts, usePrompt, useCreatePrompt, useDeletePrompt } from '../usePrompts'

// Mock the API module so no real HTTP requests are made
vi.mock('../../api/prompts', () => ({
  promptsApi: {
    list: vi.fn().mockResolvedValue({
      items: [
        {
          id: 'prompt-1',
          title: 'Email Summarizer',
          folder_id: null,
          visibility_type: 'private',
          created_by: 'user-1',
          current_version_id: 'pv-1',
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-15T10:00:00Z',
        },
        {
          id: 'prompt-2',
          title: 'Code Review Assistant',
          folder_id: 'folder-1',
          visibility_type: 'team',
          created_by: 'user-1',
          current_version_id: 'pv-2',
          created_at: '2024-01-05T00:00:00Z',
          updated_at: '2024-01-20T14:30:00Z',
        },
      ],
      total: 2,
      limit: 20,
      offset: 0,
    }),
    get: vi.fn().mockResolvedValue({
      id: 'prompt-1',
      title: 'Email Summarizer',
      folder_id: null,
      visibility_type: 'private',
      created_by: 'user-1',
      current_version_id: 'pv-1',
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-15T10:00:00Z',
    }),
    create: vi.fn().mockImplementation((data) =>
      Promise.resolve({
        id: `prompt-${Date.now()}`,
        title: data.title,
        folder_id: data.folder_id ?? null,
        visibility_type: data.visibility_type,
        created_by: 'user-1',
        current_version_id: null,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      })
    ),
    update: vi.fn(),
    delete: vi.fn().mockResolvedValue(undefined),
    listVersions: vi.fn().mockResolvedValue([]),
    getVersion: vi.fn(),
    createVersion: vi.fn(),
  },
}))

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })
  return ({ children }: { children: React.ReactNode }) =>
    React.createElement(QueryClientProvider, { client: queryClient }, children)
}

test('usePrompts returns paginated prompt data', async () => {
  const wrapper = createWrapper()
  const { result } = renderHook(() => usePrompts(), { wrapper })
  await waitFor(() => expect(result.current.isSuccess).toBe(true))
  expect(result.current.data?.items).toBeDefined()
  expect(Array.isArray(result.current.data?.items)).toBe(true)
  expect(result.current.data?.total).toBeGreaterThanOrEqual(0)
})

test('usePrompts filters by folderId', async () => {
  const { promptsApi } = await import('../../api/prompts')
  const listMock = vi.mocked(promptsApi.list)
  listMock.mockResolvedValueOnce({
    items: [
      {
        id: 'prompt-2',
        title: 'Code Review Assistant',
        folder_id: 'folder-1',
        visibility_type: 'team',
        created_by: 'user-1',
        current_version_id: 'pv-2',
        created_at: '2024-01-05T00:00:00Z',
        updated_at: '2024-01-20T14:30:00Z',
      },
    ],
    total: 1,
    limit: 20,
    offset: 0,
  })

  const wrapper = createWrapper()
  const { result } = renderHook(() => usePrompts('folder-1'), { wrapper })
  await waitFor(() => expect(result.current.isSuccess).toBe(true))
  const items = result.current.data?.items ?? []
  items.forEach((item) => {
    expect(item.folder_id).toBe('folder-1')
  })
})

test('usePrompt returns a single prompt by id', async () => {
  const wrapper = createWrapper()
  const { result } = renderHook(() => usePrompt('prompt-1'), { wrapper })
  await waitFor(() => expect(result.current.isSuccess).toBe(true))
  expect(result.current.data?.id).toBeDefined()
})

test('usePrompt is disabled when id is empty', () => {
  const wrapper = createWrapper()
  const { result } = renderHook(() => usePrompt(''), { wrapper })
  expect(result.current.fetchStatus).toBe('idle')
})

test('useCreatePrompt mutation is callable', async () => {
  const wrapper = createWrapper()
  const { result } = renderHook(() => useCreatePrompt(), { wrapper })
  let data: unknown
  await act(async () => {
    data = await result.current.mutateAsync({
      title: 'Test Prompt',
      visibility_type: 'private',
    })
  })
  await waitFor(() => expect(result.current.isSuccess).toBe(true))
  expect((data as { title: string }).title).toBe('Test Prompt')
})

test('useDeletePrompt mutation resolves', async () => {
  const wrapper = createWrapper()
  const { result } = renderHook(() => useDeletePrompt(), { wrapper })
  await act(async () => {
    await result.current.mutateAsync('prompt-1')
  })
  await waitFor(() => expect(result.current.isSuccess).toBe(true))
})
