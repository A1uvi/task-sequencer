import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { usePrompts } from '../hooks/usePrompts'
import { useFolders } from '../hooks/useFolders'
import { useDeletePrompt } from '../hooks/usePrompts'
import { LoadingSpinner } from '../components/common/LoadingSpinner'
import { EmptyState } from '../components/common/EmptyState'
import { ConfirmDialog } from '../components/common/ConfirmDialog'
import { VersionTag } from '../components/common/VersionTag'

export function PromptsPage() {
  const navigate = useNavigate()
  const [search, setSearch] = useState('')
  const [folderId, setFolderId] = useState<string | undefined>(undefined)
  const [deleteId, setDeleteId] = useState<string | null>(null)

  const { data: promptsData, isLoading, error } = usePrompts(folderId)
  const { data: folders } = useFolders()
  const deletePrompt = useDeletePrompt()

  useEffect(() => {
    document.title = 'Prompts — AI Workflow'
  }, [])

  const filteredPrompts = (promptsData?.items ?? []).filter((p) =>
    p.title.toLowerCase().includes(search.toLowerCase())
  )

  const handleDelete = async () => {
    if (!deleteId) return
    await deletePrompt.mutateAsync(deleteId)
    setDeleteId(null)
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
        Failed to load prompts. Please try again.
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Prompts</h1>
          <p className="mt-1 text-sm text-gray-500">
            Manage your prompt library and versions.
          </p>
        </div>
        <Link
          to="/prompts/new"
          className="rounded-md bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-500"
        >
          New Prompt
        </Link>
      </div>

      {/* Filters */}
      <div className="flex gap-3">
        <input
          type="text"
          placeholder="Search prompts..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="flex-1 rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
        />
        <select
          value={folderId ?? ''}
          onChange={(e) => setFolderId(e.target.value || undefined)}
          className="rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
        >
          <option value="">All folders</option>
          {(folders ?? []).map((f) => (
            <option key={f.id} value={f.id}>
              {f.name}
            </option>
          ))}
        </select>
      </div>

      {/* Prompts List */}
      {filteredPrompts.length === 0 ? (
        <EmptyState
          title="No prompts found"
          description="Create your first prompt to get started."
          action={{ label: 'New Prompt', onClick: () => navigate('/prompts/new') }}
        />
      ) : (
        <div className="overflow-hidden rounded-xl bg-white shadow-sm ring-1 ring-gray-200">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  Title
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  Version
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  Visibility
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  Last Updated
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium uppercase tracking-wider text-gray-500">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 bg-white">
              {filteredPrompts.map((prompt) => (
                <tr key={prompt.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4">
                    <Link
                      to={`/prompts/${prompt.id}`}
                      className="font-medium text-gray-900 hover:text-blue-600"
                    >
                      {prompt.title}
                    </Link>
                  </td>
                  <td className="px-6 py-4">
                    {prompt.current_version_id ? (
                      <VersionTag version={1} />
                    ) : (
                      <span className="text-xs text-gray-400">No version</span>
                    )}
                  </td>
                  <td className="px-6 py-4">
                    <span className="capitalize text-sm text-gray-600">
                      {prompt.visibility_type}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-500">
                    {new Date(prompt.updated_at).toLocaleDateString()}
                  </td>
                  <td className="px-6 py-4 text-right">
                    <button
                      type="button"
                      onClick={() => setDeleteId(prompt.id)}
                      className="text-sm text-red-600 hover:text-red-500"
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <ConfirmDialog
        isOpen={!!deleteId}
        title="Delete Prompt"
        message="Are you sure you want to delete this prompt? This action cannot be undone."
        confirmLabel="Delete"
        onConfirm={handleDelete}
        onCancel={() => setDeleteId(null)}
      />
    </div>
  )
}
