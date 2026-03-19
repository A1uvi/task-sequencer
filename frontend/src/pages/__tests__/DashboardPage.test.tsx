import React from 'react'
import { render, screen, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router-dom'
import { vi } from 'vitest'
import { DashboardPage } from '../DashboardPage'

// Mock the hooks so the page doesn't try to hit a real API
vi.mock('../../hooks/usePrompts', () => ({
  usePrompts: vi.fn().mockReturnValue({
    data: {
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
      ],
      total: 1,
      limit: 20,
      offset: 0,
    },
    isLoading: false,
    error: null,
  }),
  useDeletePrompt: vi.fn().mockReturnValue({
    mutateAsync: vi.fn().mockResolvedValue(undefined),
    isPending: false,
  }),
}))

vi.mock('../../hooks/useTasks', () => ({
  useTasks: vi.fn().mockReturnValue({
    data: {
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
      ],
      total: 1,
      limit: 20,
      offset: 0,
    },
    isLoading: false,
    error: null,
  }),
}))

vi.mock('../../hooks/useTaskExecutions', () => ({
  useTaskExecutions: vi.fn().mockReturnValue({
    data: {
      items: [
        {
          id: 'exec-1',
          task_version_id: 'tv-1',
          api_key_id: 'key-1',
          status: 'completed',
          current_step_index: 2,
          last_prompt_version_id: 'pv-2',
          step_outputs: {},
          created_by: 'user-1',
          created_at: '2024-01-15T10:00:00Z',
          updated_at: '2024-01-15T10:05:00Z',
        },
      ],
      total: 1,
      limit: 20,
      offset: 0,
    },
    isLoading: false,
    error: null,
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

test('DashboardPage renders without crashing', () => {
  render(<DashboardPage />, { wrapper })
})

test('DashboardPage renders heading', () => {
  render(<DashboardPage />, { wrapper })
  expect(screen.getByRole('heading', { name: /dashboard/i })).toBeInTheDocument()
})

test('DashboardPage renders stats cards', async () => {
  render(<DashboardPage />, { wrapper })
  await waitFor(() => {
    expect(screen.getByText(/Total Prompts/i)).toBeInTheDocument()
    expect(screen.getByText(/Total Tasks/i)).toBeInTheDocument()
    expect(screen.getByText(/Total Executions/i)).toBeInTheDocument()
  })
})

test('DashboardPage renders recent prompts section', async () => {
  render(<DashboardPage />, { wrapper })
  await waitFor(() => {
    expect(screen.getByText(/Recent Prompts/i)).toBeInTheDocument()
  })
})

test('DashboardPage renders recent tasks section', async () => {
  render(<DashboardPage />, { wrapper })
  await waitFor(() => {
    expect(screen.getByText(/Recent Tasks/i)).toBeInTheDocument()
  })
})
