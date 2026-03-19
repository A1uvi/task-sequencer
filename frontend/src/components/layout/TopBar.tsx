import React from 'react'
import { useNavigate } from 'react-router-dom'
import { useQueryClient } from '@tanstack/react-query'

export function TopBar() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const email = localStorage.getItem('user_email') ?? 'demo@example.com'

  const handleLogout = () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('user_email')
    queryClient.clear()
    navigate('/login', { replace: true })
  }

  const handleSearchShortcut = () => {
    navigate('/search')
  }

  React.useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault()
        handleSearchShortcut()
      }
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [])

  return (
    <header className="flex h-16 items-center justify-between border-b border-gray-200 bg-white px-6">
      <button
        type="button"
        onClick={handleSearchShortcut}
        className="flex items-center gap-2 rounded-lg border border-gray-300 bg-gray-50 px-4 py-2 text-sm text-gray-500 hover:bg-gray-100"
      >
        <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
        Search...
        <kbd className="ml-2 hidden rounded border border-gray-300 bg-white px-1.5 py-0.5 text-xs text-gray-500 sm:inline-block">
          Cmd+K
        </kbd>
      </button>

      <div className="flex items-center gap-4">
        <span className="text-sm text-gray-600">{email}</span>
        <button
          type="button"
          onClick={handleLogout}
          className="rounded-md border border-gray-300 bg-white px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          Logout
        </button>
      </div>
    </header>
  )
}
