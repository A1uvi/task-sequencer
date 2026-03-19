import React from 'react'
import { renderHook, waitFor, act } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { vi } from 'vitest'
import { useTasks, useTask, useCreateTask, useTaskVersions } from '../useTasks'

// Mock the API module so no real HTTP requests are made
vi.mock('../../api/tasks', () => ({
  tasksApi: {
    list: vi.fn().mockResolvedValue({
      items: [
        {
          id: 'task-1',
          title: 'Email Processing Pipeline',
          folder_id: null,
          visibility_type: 'private',
          created_by: 'user-1',
          current_version_id: 'tv-1',
          created_at: '2024-01-02T00:00:00Z',
          updated_at: '2024-01-16T11:00:00Z',
        },
        {
          id: 'task-2',
          title: 'Code Review Workflow',
          folder_id: 'folder-1',
          visibility_type: 'team',
          created_by: 'user-1',
          current_version_id: 'tv-2',
          created_at: '2024-01-07T00:00:00Z',
          updated_at: '2024-01-21T15:00:00Z',
        },
      ],
      total: 2,
      limit: 20,
      offset: 0,
    }),
    get: vi.fn().mockResolvedValue({
      id: 'task-1',
      title: 'Email Processing Pipeline',
      folder_id: null,
      visibility_type: 'private',
      created_by: 'user-1',
      current_version_id: 'tv-1',
      created_at: '2024-01-02T00:00:00Z',
      updated_at: '2024-01-16T11:00:00Z',
    }),
    create: vi.fn().mockImplementation((data) =>
      Promise.resolve({
        id: `task-${Date.now()}`,
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
    listVersions: vi.fn().mockResolvedValue([
      {
        id: 'tv-1',
        task_id: 'task-1',
        ordered_prompt_version_ids: ['pv-1', 'pv-2'],
        default_model: 'gpt-4o',
        allow_model_override_per_step: false,
        version_number: 1,
        created_at: '2024-01-02T00:00:00Z',
      },
    ]),
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

test('useTasks returns paginated task data', async () => {
  const wrapper = createWrapper()
  const { result } = renderHook(() => useTasks(), { wrapper })
  await waitFor(() => expect(result.current.isSuccess).toBe(true))
  expect(result.current.data?.items).toBeDefined()
  expect(Array.isArray(result.current.data?.items)).toBe(true)
  expect(result.current.data?.total).toBeGreaterThanOrEqual(0)
})

test('useTasks filters by folderId', async () => {
  const { tasksApi } = await import('../../api/tasks')
  const listMock = vi.mocked(tasksApi.list)
  listMock.mockResolvedValueOnce({
    items: [
      {
        id: 'task-2',
        title: 'Code Review Workflow',
        folder_id: 'folder-1',
        visibility_type: 'team',
        created_by: 'user-1',
        current_version_id: 'tv-2',
        created_at: '2024-01-07T00:00:00Z',
        updated_at: '2024-01-21T15:00:00Z',
      },
    ],
    total: 1,
    limit: 20,
    offset: 0,
  })

  const wrapper = createWrapper()
  const { result } = renderHook(() => useTasks('folder-1'), { wrapper })
  await waitFor(() => expect(result.current.isSuccess).toBe(true))
  const items = result.current.data?.items ?? []
  items.forEach((item) => {
    expect(item.folder_id).toBe('folder-1')
  })
})

test('useTask returns a single task by id', async () => {
  const wrapper = createWrapper()
  const { result } = renderHook(() => useTask('task-1'), { wrapper })
  await waitFor(() => expect(result.current.isSuccess).toBe(true))
  expect(result.current.data?.id).toBeDefined()
})

test('useTask is disabled when id is empty', () => {
  const wrapper = createWrapper()
  const { result } = renderHook(() => useTask(''), { wrapper })
  expect(result.current.fetchStatus).toBe('idle')
})

test('useCreateTask mutation creates a task', async () => {
  const wrapper = createWrapper()
  const { result } = renderHook(() => useCreateTask(), { wrapper })
  let data: unknown
  await act(async () => {
    data = await result.current.mutateAsync({
      title: 'New Task',
      visibility_type: 'private',
    })
  })
  await waitFor(() => expect(result.current.isSuccess).toBe(true))
  expect((data as { title: string }).title).toBe('New Task')
})

test('useTaskVersions returns versions for a task', async () => {
  const wrapper = createWrapper()
  const { result } = renderHook(() => useTaskVersions('task-1'), { wrapper })
  await waitFor(() => expect(result.current.isSuccess).toBe(true))
  expect(Array.isArray(result.current.data)).toBe(true)
})

test('useTaskVersions is disabled when taskId is empty', () => {
  const wrapper = createWrapper()
  const { result } = renderHook(() => useTaskVersions(''), { wrapper })
  expect(result.current.fetchStatus).toBe('idle')
})
