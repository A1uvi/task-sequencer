import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { usePrompt, usePromptVersions, useCreatePrompt, useUpdatePrompt, useCreatePromptVersion } from '../hooks/usePrompts'
import { useCreateTaskExecution } from '../hooks/useTaskExecutions'
import { LoadingSpinner } from '../components/common/LoadingSpinner'
import { VersionTag } from '../components/common/VersionTag'
import { VisibilityType } from '../types'

export function PromptEditorPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const isNew = !id || id === 'new'

  const { data: prompt, isLoading: promptLoading } = usePrompt(isNew ? '' : id)
  const { data: versions } = usePromptVersions(isNew ? '' : (id ?? ''))

  const createPrompt = useCreatePrompt()
  const updatePrompt = useUpdatePrompt()
  const createVersion = useCreatePromptVersion()
  const createExecution = useCreateTaskExecution()

  const [title, setTitle] = useState('')
  const [content, setContent] = useState('')
  const [usageNotes, setUsageNotes] = useState('')
  const [tags, setTags] = useState('')
  const [visibility, setVisibility] = useState<VisibilityType>('private')
  const [isSaving, setIsSaving] = useState(false)
  const [saveError, setSaveError] = useState<string | null>(null)

  useEffect(() => {
    document.title = isNew ? 'New Prompt — AI Workflow' : `Edit Prompt — AI Workflow`
  }, [isNew])

  useEffect(() => {
    if (prompt) {
      setTitle(prompt.title)
      setVisibility(prompt.visibility_type)
    }
  }, [prompt])

  const handleSave = async () => {
    setSaveError(null)
    setIsSaving(true)
    try {
      let promptId = id
      if (isNew) {
        const newPrompt = await createPrompt.mutateAsync({
          title,
          visibility_type: visibility,
        })
        promptId = newPrompt.id
      } else {
        await updatePrompt.mutateAsync({ id: id!, data: { title, visibility_type: visibility } })
      }

      if (content.trim()) {
        await createVersion.mutateAsync({
          promptId: promptId!,
          data: {
            content,
            usage_notes: usageNotes || undefined,
            tags: tags ? tags.split(',').map((t) => t.trim()).filter(Boolean) : [],
          },
        })
      }

      if (isNew && promptId) {
        navigate(`/prompts/${promptId}`)
      }
    } catch {
      setSaveError('Failed to save. Please try again.')
    } finally {
      setIsSaving(false)
    }
  }

  const handleRun = async () => {
    try {
      const execution = await createExecution.mutateAsync({
        task_version_id: 'tv-1',
        api_key_id: 'key-1',
      })
      navigate(`/executions/${execution.id}`)
    } catch {
      setSaveError('Failed to start execution. Please try again.')
    }
  }

  if (!isNew && promptLoading) {
    return (
      <div className="flex h-full items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">
          {isNew ? 'New Prompt' : 'Edit Prompt'}
        </h1>
        <div className="flex gap-3">
          <button
            type="button"
            onClick={handleRun}
            disabled={createExecution.isPending}
            className="rounded-md border border-green-600 px-4 py-2 text-sm font-medium text-green-600 hover:bg-green-50 disabled:opacity-50"
          >
            Run
          </button>
          <button
            type="button"
            onClick={handleSave}
            disabled={isSaving}
            className="flex items-center gap-2 rounded-md bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-500 disabled:opacity-50"
          >
            {isSaving && <LoadingSpinner size="sm" />}
            Save as New Version
          </button>
        </div>
      </div>

      {saveError && (
        <div className="rounded-md bg-red-50 p-3 text-sm text-red-700">
          {saveError}
        </div>
      )}

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Left: Editor */}
        <div className="space-y-4 lg:col-span-2">
          <div className="rounded-xl bg-white p-6 shadow-sm ring-1 ring-gray-200">
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Title
                </label>
                <input
                  type="text"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="e.g., Email Summarizer"
                  className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Visibility
                </label>
                <select
                  value={visibility}
                  onChange={(e) => setVisibility(e.target.value as VisibilityType)}
                  className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                >
                  <option value="private">Private</option>
                  <option value="team">Team</option>
                  <option value="public">Public</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Prompt Content
                </label>
                <textarea
                  value={content}
                  onChange={(e) => setContent(e.target.value)}
                  rows={12}
                  placeholder="Write your prompt here. Use {{variable}} syntax for variables."
                  className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 font-mono text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Usage Notes
                </label>
                <textarea
                  value={usageNotes}
                  onChange={(e) => setUsageNotes(e.target.value)}
                  rows={3}
                  placeholder="Notes about when and how to use this prompt..."
                  className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Tags (comma-separated)
                </label>
                <input
                  type="text"
                  value={tags}
                  onChange={(e) => setTags(e.target.value)}
                  placeholder="e.g., email, summarization, business"
                  className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                />
              </div>
            </div>
          </div>
        </div>

        {/* Right: Version History */}
        <div className="rounded-xl bg-white p-6 shadow-sm ring-1 ring-gray-200">
          <h2 className="text-base font-semibold text-gray-900">Version History</h2>
          {!id || isNew ? (
            <p className="mt-3 text-sm text-gray-500">
              Save your first version to see history here.
            </p>
          ) : (versions ?? []).length === 0 ? (
            <p className="mt-3 text-sm text-gray-500">No versions yet.</p>
          ) : (
            <ul className="mt-4 space-y-3">
              {(versions ?? []).map((v) => (
                <li
                  key={v.id}
                  className="rounded-lg border border-gray-100 p-3"
                >
                  <div className="flex items-center justify-between">
                    <VersionTag version={v.version_number} />
                    <span className="text-xs text-gray-400">
                      {new Date(v.created_at).toLocaleDateString()}
                    </span>
                  </div>
                  {v.tags.length > 0 && (
                    <div className="mt-2 flex flex-wrap gap-1">
                      {v.tags.map((tag) => (
                        <span
                          key={tag}
                          className="rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-600"
                        >
                          {tag}
                        </span>
                      ))}
                    </div>
                  )}
                  <p className="mt-2 text-xs text-gray-500 line-clamp-2">
                    {v.content}
                  </p>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  )
}
