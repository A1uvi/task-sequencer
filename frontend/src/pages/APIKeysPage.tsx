import React, { useEffect, useState } from 'react'
import { useApiKeys, useCreateApiKey, useRevokeApiKey, useShareApiKey } from '../hooks/useApiKeys'
import { LoadingSpinner } from '../components/common/LoadingSpinner'
import { EmptyState } from '../components/common/EmptyState'
import { StatusBadge } from '../components/common/StatusBadge'
import { ProviderIcon } from '../components/common/ProviderIcon'
import { ConfirmDialog } from '../components/common/ConfirmDialog'
import { APIKeyOwnerType } from '../types'

const PROVIDERS = ['openai', 'anthropic', 'google']

export function APIKeysPage() {
  const { data: apiKeys, isLoading, error } = useApiKeys()
  const createKey = useCreateApiKey()
  const revokeKey = useRevokeApiKey()
  const shareKey = useShareApiKey()

  const [showAddForm, setShowAddForm] = useState(false)
  const [provider, setProvider] = useState('openai')
  const [keyInput, setKeyInput] = useState('')
  const [maskedInput, setMaskedInput] = useState('')
  const [isKeyMasked, setIsKeyMasked] = useState(false)
  const [ownerType] = useState<APIKeyOwnerType>('user')
  const [revokeId, setRevokeId] = useState<string | null>(null)
  const [shareId, setShareId] = useState<string | null>(null)
  const [shareUserId, setShareUserId] = useState('')
  const [formError, setFormError] = useState<string | null>(null)

  useEffect(() => {
    document.title = 'API Keys — AI Workflow'
  }, [])

  const handleKeyBlur = () => {
    if (keyInput && !isKeyMasked) {
      setMaskedInput(`••••••••••••${keyInput.slice(-4)}`)
      setIsKeyMasked(true)
    }
  }

  const handleAddKey = async (e: React.FormEvent) => {
    e.preventDefault()
    setFormError(null)
    if (!keyInput && !isKeyMasked) {
      setFormError('Please enter an API key.')
      return
    }
    try {
      await createKey.mutateAsync({
        provider,
        key: keyInput || '****',
        owner_type: ownerType,
        owner_id: 'user-1',
      })
      setShowAddForm(false)
      setKeyInput('')
      setMaskedInput('')
      setIsKeyMasked(false)
    } catch {
      setFormError('Failed to add API key. Please try again.')
    }
  }

  const handleRevoke = async () => {
    if (!revokeId) return
    await revokeKey.mutateAsync(revokeId)
    setRevokeId(null)
  }

  const handleShare = async () => {
    if (!shareId || !shareUserId.trim()) return
    await shareKey.mutateAsync({
      id: shareId,
      data: { user_ids: [shareUserId.trim()] },
    })
    setShareId(null)
    setShareUserId('')
  }

  if (isLoading) {
    return (
      <div className="flex h-full items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="rounded-md bg-red-50 p-4 text-sm text-red-700">
        Failed to load API keys. Please try again.
      </div>
    )
  }

  const keys = apiKeys ?? []

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">API Keys</h1>
          <p className="mt-1 text-sm text-gray-500">
            Manage your AI provider API keys.
          </p>
        </div>
        <button
          type="button"
          onClick={() => setShowAddForm((v) => !v)}
          className="rounded-md bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-500"
        >
          {showAddForm ? 'Cancel' : 'Add Key'}
        </button>
      </div>

      {/* Add Key Form */}
      {showAddForm && (
        <div className="rounded-xl bg-white p-6 shadow-sm ring-1 ring-gray-200">
          <h2 className="mb-4 text-base font-semibold text-gray-900">Add New API Key</h2>
          <form onSubmit={handleAddKey} className="space-y-4">
            {formError && (
              <div className="rounded-md bg-red-50 p-3 text-sm text-red-700">
                {formError}
              </div>
            )}
            <div>
              <label className="block text-sm font-medium text-gray-700">Provider</label>
              <select
                value={provider}
                onChange={(e) => setProvider(e.target.value)}
                className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
              >
                {PROVIDERS.map((p) => (
                  <option key={p} value={p}>
                    {p.charAt(0).toUpperCase() + p.slice(1)}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">
                API Key
              </label>
              <input
                type={isKeyMasked ? 'text' : 'password'}
                value={isKeyMasked ? maskedInput : keyInput}
                onChange={(e) => {
                  if (!isKeyMasked) setKeyInput(e.target.value)
                }}
                onBlur={handleKeyBlur}
                placeholder="Paste your API key here..."
                readOnly={isKeyMasked}
                className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 font-mono text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
              />
              {isKeyMasked && (
                <p className="mt-1 text-xs text-gray-500">
                  Key masked for security. Only the last 4 characters are shown.
                </p>
              )}
            </div>
            <button
              type="submit"
              disabled={createKey.isPending}
              className="flex items-center gap-2 rounded-md bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-500 disabled:opacity-50"
            >
              {createKey.isPending && <LoadingSpinner size="sm" />}
              Save API Key
            </button>
          </form>
        </div>
      )}

      {/* Keys List */}
      {keys.length === 0 ? (
        <EmptyState
          title="No API keys"
          description="Add an API key to start using AI providers."
          action={{ label: 'Add Key', onClick: () => setShowAddForm(true) }}
        />
      ) : (
        <div className="overflow-hidden rounded-xl bg-white shadow-sm ring-1 ring-gray-200">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  Provider
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  Key
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  Owner
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  Shared With
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  Added
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium uppercase tracking-wider text-gray-500">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 bg-white">
              {keys.map((key) => (
                <tr key={key.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4">
                    <ProviderIcon provider={key.provider} />
                  </td>
                  <td className="px-6 py-4 font-mono text-sm text-gray-900">
                    {key.masked_key}
                  </td>
                  <td className="px-6 py-4">
                    <StatusBadge status={key.status} />
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-600 capitalize">
                    {key.owner_type}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-600">
                    {key.shared_with_users.length + key.shared_with_teams.length > 0
                      ? `${key.shared_with_users.length} user(s), ${key.shared_with_teams.length} team(s)`
                      : 'Not shared'}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-500">
                    {new Date(key.created_at).toLocaleDateString()}
                  </td>
                  <td className="px-6 py-4 text-right">
                    <div className="flex justify-end gap-3">
                      <button
                        type="button"
                        onClick={() => setShareId(key.id)}
                        className="text-sm text-blue-600 hover:text-blue-500"
                      >
                        Share
                      </button>
                      {key.status !== 'revoked' && (
                        <button
                          type="button"
                          onClick={() => setRevokeId(key.id)}
                          className="text-sm text-red-600 hover:text-red-500"
                        >
                          Revoke
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Revoke Confirm Dialog */}
      <ConfirmDialog
        isOpen={!!revokeId}
        title="Revoke API Key"
        message="Are you sure you want to revoke this API key? This action cannot be undone."
        confirmLabel="Revoke"
        onConfirm={handleRevoke}
        onCancel={() => setRevokeId(null)}
      />

      {/* Share Dialog */}
      {shareId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div
            className="absolute inset-0 bg-black bg-opacity-50"
            onClick={() => setShareId(null)}
            aria-hidden="true"
          />
          <div className="relative z-10 w-full max-w-md rounded-lg bg-white p-6 shadow-xl">
            <h2 className="text-lg font-semibold text-gray-900">Share API Key</h2>
            <p className="mt-2 text-sm text-gray-600">
              Enter the user ID to share this key with.
            </p>
            <input
              type="text"
              value={shareUserId}
              onChange={(e) => setShareUserId(e.target.value)}
              placeholder="User ID"
              className="mt-4 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
            <div className="mt-6 flex justify-end gap-3">
              <button
                type="button"
                onClick={() => setShareId(null)}
                className="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleShare}
                disabled={!shareUserId.trim() || shareKey.isPending}
                className="flex items-center gap-2 rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-500 disabled:opacity-50"
              >
                {shareKey.isPending && <LoadingSpinner size="sm" />}
                Share
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
