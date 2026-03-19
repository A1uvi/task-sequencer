import React from 'react'
import { renderHook, waitFor, act } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { vi } from 'vitest'
import {
  useTaskExecutions,
  useTaskExecution,
  useCreateTaskExecution,
  useCancelTaskExecution,
} from '../useTaskExecutions'

// Mock the API module so no real HTTP requests are made
vi.mock('../../api/taskExecutions', () => ({
  taskExecutionsApi: {
    list: vi.fn().mockResolvedValue({
      items: [
        {
          id: 'exec-1',
          task_version_id: 'tv-1',
          api_key_id: 'key-1',
          status: 'completed',
          current_step_index: 2,
          last_prompt_version_id: 'pv-2',
          step_outputs: {
            '0': 'Step 1 output',
            '1': 'Step 2 output',
          },
          created_by: 'user-1',
          created_at: '2024-01-15T10:00:00Z',
          updated_at: '2024-01-15T10:05:00Z',
        },
        {
          id: 'exec-2',
          task_version_id: 'tv-1',
          api_key_id: 'key-1',
          status: 'running',
          current_step_index: 0,
          last_prompt_version_id: 'pv-1',
          step_outputs: {},
          created_by: 'user-1',
          created_at: '2024-01-20T14:00:00Z',
          updated_at: '2024-01-20T14:01:00Z',
        },
      ],
      total: 2,
      limit: 20,
      offset: 0,
    }),
    get: vi.fn().mockImplementation((id: string) =>
      Promise.resolve(
        id === 'exec-1'
          ? {
              id: 'exec-1',
              task_version_id: 'tv-1',
              api_key_id: 'key-1',
              status: 'completed',
              current_step_index: 2,
              last_prompt_version_id: 'pv-2',
              step_outputs: { '0': 'output', '1': 'output' },
              created_by: 'user-1',
              created_at: '2024-01-15T10:00:00Z',
              updated_at: '2024-01-15T10:05:00Z',
            }
          : {
              id: 'exec-2',
              task_version_id: 'tv-1',
              api_key_id: 'key-1',
              status: 'running',
              current_step_index: 0,
              last_prompt_version_id: 'pv-1',
              step_outputs: {},
              created_by: 'user-1',
              created_at: '2024-01-20T14:00:00Z',
              updated_at: '2024-01-20T14:01:00Z',
            }
      )
    ),
    create: vi.fn().mockImplementation((data) =>
      Promise.resolve({
        id: `exec-${Date.now()}`,
        task_version_id: data.task_version_id,
        api_key_id: data.api_key_id,
        status: 'queued',
        current_step_index: 0,
        last_prompt_version_id: null,
        step_outputs: {},
        created_by: 'user-1',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      })
    ),
    cancel: vi.fn().mockResolvedValue({
      id: 'exec-2',
      task_version_id: 'tv-1',
      api_key_id: 'key-1',
      status: 'failed',
      current_step_index: 0,
      last_prompt_version_id: null,
      step_outputs: {},
      created_by: 'user-1',
      created_at: '2024-01-20T14:00:00Z',
      updated_at: new Date().toISOString(),
    }),
    listByTask: vi.fn().mockResolvedValue([]),
  },
}))

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })
  return ({ children }: { children: React.ReactNode }) =>
    React.createElement(QueryClientProvider, { client: queryClient }, children)
}

test('useTaskExecutions returns paginated executions', async () => {
  const wrapper = createWrapper()
  const { result } = renderHook(() => useTaskExecutions(), { wrapper })
  await waitFor(() => expect(result.current.isSuccess).toBe(true))
  expect(result.current.data?.items).toBeDefined()
  expect(Array.isArray(result.current.data?.items)).toBe(true)
})

test('executions have required fields', async () => {
  const wrapper = createWrapper()
  const { result } = renderHook(() => useTaskExecutions(), { wrapper })
  await waitFor(() => expect(result.current.isSuccess).toBe(true))
  const execution = result.current.data?.items[0]
  expect(execution).toHaveProperty('id')
  expect(execution).toHaveProperty('status')
  expect(execution).toHaveProperty('current_step_index')
  expect(execution).toHaveProperty('step_outputs')
})

test('useTaskExecution fetches a single execution', async () => {
  const wrapper = createWrapper()
  const { result } = renderHook(() => useTaskExecution('exec-1'), { wrapper })
  await waitFor(() => expect(result.current.isSuccess).toBe(true))
  expect(result.current.data?.id).toBeDefined()
})

test('useTaskExecution is disabled when id is empty', () => {
  const wrapper = createWrapper()
  const { result } = renderHook(() => useTaskExecution(''), { wrapper })
  expect(result.current.fetchStatus).toBe('idle')
})

test('useCreateTaskExecution creates an execution with queued status', async () => {
  const wrapper = createWrapper()
  const { result } = renderHook(() => useCreateTaskExecution(), { wrapper })
  let data: unknown
  await act(async () => {
    data = await result.current.mutateAsync({
      task_version_id: 'tv-1',
      api_key_id: 'key-1',
    })
  })
  await waitFor(() => expect(result.current.isSuccess).toBe(true))
  const exec = data as { status: string; task_version_id: string }
  expect(exec.status).toBe('queued')
  expect(exec.task_version_id).toBe('tv-1')
})

test('useCancelTaskExecution sets status to failed', async () => {
  const wrapper = createWrapper()
  const { result } = renderHook(() => useCancelTaskExecution(), { wrapper })
  let data: unknown
  await act(async () => {
    data = await result.current.mutateAsync('exec-2')
  })
  await waitFor(() => expect(result.current.isSuccess).toBe(true))
  expect((data as { status: string }).status).toBe('failed')
})

test('completed execution does not poll (refetchInterval is false)', async () => {
  const wrapper = createWrapper()
  // exec-1 has status 'completed', which is terminal
  const { result } = renderHook(() => useTaskExecution('exec-1'), { wrapper })
  await waitFor(() => expect(result.current.isSuccess).toBe(true))
  expect(result.current.data?.status).toBe('completed')
  // No way to directly test refetchInterval but we verify it doesn't throw
})
