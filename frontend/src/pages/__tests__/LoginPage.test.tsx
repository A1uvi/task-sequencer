import React from 'react'
import { render, screen } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router-dom'
import { LoginPage } from '../LoginPage'

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

test('LoginPage renders without crashing', () => {
  render(<LoginPage />, { wrapper })
})

test('LoginPage renders email and password fields', () => {
  render(<LoginPage />, { wrapper })
  expect(screen.getByLabelText(/email address/i)).toBeInTheDocument()
  expect(screen.getByLabelText(/password/i)).toBeInTheDocument()
})

test('LoginPage renders sign in button', () => {
  render(<LoginPage />, { wrapper })
  expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument()
})

test('LoginPage renders register link', () => {
  render(<LoginPage />, { wrapper })
  expect(screen.getByRole('button', { name: /register/i })).toBeInTheDocument()
})

test('LoginPage renders app title', () => {
  render(<LoginPage />, { wrapper })
  expect(screen.getByText(/AI Workflow Platform/i)).toBeInTheDocument()
})
