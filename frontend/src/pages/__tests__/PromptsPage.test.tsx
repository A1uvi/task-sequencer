import React from 'react'
import { render, screen, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router-dom'
import { vi } from 'vitest'
import { PromptsPage } from '../PromptsPage'

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
    },
    isLoading: false,
    error: null,
  }),
  useDeletePrompt: vi.fn().mockReturnValue({
    mutateAsync: vi.fn().mockResolvedValue(undefined),
    isPending: false,
  }),
}))

vi.mock('../../hooks/useFolders', () => ({
  useFolders: vi.fn().mockReturnValue({
    data: [
      {
        id: 'folder-1',
        name: 'Work Projects',
        visibility_type: 'team',
        team_ids: ['team-1'],
        created_by: 'user-1',
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      },
    ],
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

test('PromptsPage renders without crashing', () => {
  render(<PromptsPage />, { wrapper })
})

test('PromptsPage renders heading', () => {
  render(<PromptsPage />, { wrapper })
  expect(screen.getByRole('heading', { name: /prompts/i })).toBeInTheDocument()
})

test('PromptsPage renders search input', () => {
  render(<PromptsPage />, { wrapper })
  expect(screen.getByPlaceholderText(/search prompts/i)).toBeInTheDocument()
})

test('PromptsPage renders New Prompt button', () => {
  render(<PromptsPage />, { wrapper })
  expect(screen.getByRole('link', { name: /new prompt/i })).toBeInTheDocument()
})

test('PromptsPage renders prompt items after loading', async () => {
  render(<PromptsPage />, { wrapper })
  await waitFor(() => {
    expect(screen.getByText(/Email Summarizer/i)).toBeInTheDocument()
  })
})

test('PromptsPage renders folder filter dropdown', () => {
  render(<PromptsPage />, { wrapper })
  expect(screen.getByText(/All folders/i)).toBeInTheDocument()
})
