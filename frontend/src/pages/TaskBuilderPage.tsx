import { useEffect, useRef, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useTask, useTaskVersions, useCreateTask, useCreateTaskVersion } from '../hooks/useTasks'
import { usePrompts } from '../hooks/usePrompts'
import { useApiKeys } from '../hooks/useApiKeys'
import { useCreateTaskExecution } from '../hooks/useTaskExecutions'
import { LoadingSpinner } from '../components/common/LoadingSpinner'
import { EmptyState } from '../components/common/EmptyState'
import { VersionTag } from '../components/common/VersionTag'
import { Attachment, TaskStep, VisibilityType } from '../types'

const MODELS = [
  { label: 'GPT-4o', value: 'gpt-4o', provider: 'openai' },
  { label: 'GPT-4o Mini', value: 'gpt-4o-mini', provider: 'openai' },
  { label: 'Claude 3.5 Sonnet', value: 'claude-3-5-sonnet-20241022', provider: 'anthropic' },
  { label: 'Claude 3 Haiku', value: 'claude-3-haiku-20240307', provider: 'anthropic' },
  { label: 'Gemini 1.5 Pro', value: 'gemini-1.5-pro', provider: 'google' },
]

export function TaskBuilderPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const isNew = !id

  const { data: task, isLoading: taskLoading } = useTask(isNew ? '' : id)
  const { data: versions } = useTaskVersions(isNew ? '' : (id ?? ''))
  const { data: promptsData } = usePrompts()
  const { data: apiKeys } = useApiKeys()

  const createTask = useCreateTask()
  const createVersion = useCreateTaskVersion()
  const createExecution = useCreateTaskExecution()

  const [title, setTitle] = useState('')
  const [visibility, setVisibility] = useState<VisibilityType>('private')
  const [steps, setSteps] = useState<TaskStep[]>([])
  const [defaultModel, setDefaultModel] = useState('gpt-4o')
  const [allowModelOverride, setAllowModelOverride] = useState(false)
  const [selectedApiKeyId, setSelectedApiKeyId] = useState('')
  const [isSaving, setIsSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Add step mode: 'library' | 'local'
  const [addMode, setAddMode] = useState<'library' | 'local'>('library')
  const [localContent, setLocalContent] = useState('')
  const [localAttachments, setLocalAttachments] = useState<Attachment[]>([])
  const fileInputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    document.title = isNew ? 'New Task — AI Workflow' : 'Edit Task — AI Workflow'
  }, [isNew])

  useEffect(() => {
    if (task) {
      setTitle(task.title)
      setVisibility(task.visibility_type)
    }
  }, [task])

  useEffect(() => {
    if (apiKeys && apiKeys.length > 0 && !selectedApiKeyId) {
      setSelectedApiKeyId(apiKeys[0].id)
    }
  }, [apiKeys, selectedApiKeyId])

  const handleAddLibraryStep = (promptVersionId: string) => {
    setSteps((prev) => [...prev, { type: 'library', prompt_version_id: promptVersionId }])
  }

  const handleFilesSelected = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files ?? [])
    files.forEach((file) => {
      const reader = new FileReader()
      reader.onload = (ev) => {
        const dataUrl = ev.target?.result as string
        // Strip "data:<content_type>;base64," prefix
        const base64 = dataUrl.split(',')[1] ?? ''
        setLocalAttachments((prev) => [
          ...prev,
          { filename: file.name, content_type: file.type || 'application/octet-stream', data: base64 },
        ])
      }
      reader.readAsDataURL(file)
    })
    // Reset input so same file can be re-selected
    if (fileInputRef.current) fileInputRef.current.value = ''
  }

  const handleAddLocalStep = () => {
    if (!localContent.trim()) return
    setSteps((prev) => [
      ...prev,
      { type: 'local', content: localContent, attachments: localAttachments },
    ])
    setLocalContent('')
    setLocalAttachments([])
  }

  const handleRemoveStep = (index: number) => {
    setSteps((prev) => prev.filter((_, i) => i !== index))
  }

  const handleMoveUp = (index: number) => {
    if (index === 0) return
    setSteps((prev) => {
      const next = [...prev]
      ;[next[index - 1], next[index]] = [next[index], next[index - 1]]
      return next
    })
  }

  const handleMoveDown = (index: number) => {
    setSteps((prev) => {
      if (index === prev.length - 1) return prev
      const next = [...prev]
      ;[next[index], next[index + 1]] = [next[index + 1], next[index]]
      return next
    })
  }

  const handleSave = async () => {
    setError(null)
    setIsSaving(true)
    try {
      let taskId = id
      if (isNew) {
        const newTask = await createTask.mutateAsync({ title, visibility_type: visibility })
        taskId = newTask.id
      }
      await createVersion.mutateAsync({
        taskId: taskId!,
        data: {
          steps,
          default_model: defaultModel,
          allow_model_override_per_step: allowModelOverride,
        },
      })
      if (isNew && taskId) {
        navigate(`/tasks/${taskId}`)
      }
    } catch {
      setError('Failed to save task. Please try again.')
    } finally {
      setIsSaving(false)
    }
  }

  const handleRun = async () => {
    try {
      const versionId = versions?.[0]?.id ?? 'tv-1'
      const execution = await createExecution.mutateAsync({
        task_version_id: versionId,
        api_key_id: selectedApiKeyId || 'key-1',
      })
      navigate(`/executions/${execution.id}`)
    } catch {
      setError('Failed to start execution.')
    }
  }

  if (!isNew && taskLoading) {
    return (
      <div className="flex h-full items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  const prompts = promptsData?.items ?? []

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">
          {isNew ? 'New Task' : 'Edit Task'}
        </h1>
        <div className="flex gap-3">
          <button
            type="button"
            onClick={handleRun}
            disabled={createExecution.isPending}
            className="rounded-md border border-green-600 px-4 py-2 text-sm font-medium text-green-600 hover:bg-green-50 disabled:opacity-50"
          >
            Run Task
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

      {error && (
        <div className="rounded-md bg-red-50 p-3 text-sm text-red-700">{error}</div>
      )}

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="space-y-6 lg:col-span-2">
          {/* Task Details */}
          <div className="rounded-xl bg-white p-6 shadow-sm ring-1 ring-gray-200">
            <h2 className="mb-4 text-base font-semibold text-gray-900">Task Details</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Title</label>
                <input
                  type="text"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="e.g., Email Processing Pipeline"
                  className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Visibility</label>
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
            </div>
          </div>

          {/* Steps */}
          <div className="rounded-xl bg-white p-6 shadow-sm ring-1 ring-gray-200">
            <h2 className="mb-4 text-base font-semibold text-gray-900">Prompt Steps</h2>

            {steps.length === 0 ? (
              <EmptyState
                title="No steps yet"
                description="Add prompt steps to build your task pipeline."
              />
            ) : (
              <ol className="space-y-3">
                {steps.map((step, index) => {
                  const label =
                    step.type === 'library'
                      ? (prompts.find(
                          (p) => p.current_version_id === step.prompt_version_id || p.id === step.prompt_version_id
                        )?.title ?? `Step ${index + 1} (${step.prompt_version_id})`)
                      : `Local — ${step.content.slice(0, 60)}${step.content.length > 60 ? '…' : ''}${step.attachments.length > 0 ? ` [${step.attachments.length} file(s)]` : ''}`
                  return (
                    <li
                      key={index}
                      className="flex items-center gap-3 rounded-lg border border-gray-200 p-3"
                    >
                      <span className="flex h-6 w-6 flex-shrink-0 items-center justify-center rounded-full bg-blue-100 text-xs font-semibold text-blue-700">
                        {index + 1}
                      </span>
                      <span className="flex-1 text-sm font-medium text-gray-900">{label}</span>
                      <div className="flex gap-1">
                        <button
                          type="button"
                          onClick={() => handleMoveUp(index)}
                          disabled={index === 0}
                          className="rounded p-1 text-gray-400 hover:text-gray-600 disabled:opacity-30"
                          title="Move up"
                        >
                          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
                          </svg>
                        </button>
                        <button
                          type="button"
                          onClick={() => handleMoveDown(index)}
                          disabled={index === steps.length - 1}
                          className="rounded p-1 text-gray-400 hover:text-gray-600 disabled:opacity-30"
                          title="Move down"
                        >
                          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                          </svg>
                        </button>
                        <button
                          type="button"
                          onClick={() => handleRemoveStep(index)}
                          className="rounded p-1 text-red-400 hover:text-red-600"
                          title="Remove step"
                        >
                          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                          </svg>
                        </button>
                      </div>
                    </li>
                  )
                })}
              </ol>
            )}

            {/* Add step section */}
            <div className="mt-4 space-y-3">
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => setAddMode('library')}
                  className={`rounded-md px-3 py-1.5 text-sm font-medium ${addMode === 'library' ? 'bg-blue-100 text-blue-700' : 'text-gray-600 hover:bg-gray-100'}`}
                >
                  From library
                </button>
                <button
                  type="button"
                  onClick={() => setAddMode('local')}
                  className={`rounded-md px-3 py-1.5 text-sm font-medium ${addMode === 'local' ? 'bg-blue-100 text-blue-700' : 'text-gray-600 hover:bg-gray-100'}`}
                >
                  Create local prompt
                </button>
              </div>

              {addMode === 'library' ? (
                <div>
                  <label className="block text-sm font-medium text-gray-700">Add Step</label>
                  <select
                    onChange={(e) => {
                      if (e.target.value) {
                        handleAddLibraryStep(e.target.value)
                        e.target.value = ''
                      }
                    }}
                    className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                    defaultValue=""
                  >
                    <option value="">Select a prompt to add...</option>
                    {prompts.map((p) => (
                      <option key={p.id} value={p.current_version_id ?? p.id}>
                        {p.title}
                      </option>
                    ))}
                  </select>
                </div>
              ) : (
                <div className="space-y-3 rounded-lg border border-blue-100 bg-blue-50 p-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Prompt text</label>
                    <textarea
                      value={localContent}
                      onChange={(e) => setLocalContent(e.target.value)}
                      rows={4}
                      placeholder="Enter your prompt text here..."
                      className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">
                      Attachments (optional)
                    </label>
                    <input
                      ref={fileInputRef}
                      type="file"
                      multiple
                      accept="image/jpeg,image/png,image/gif,image/webp,text/plain,text/markdown,application/pdf"
                      onChange={handleFilesSelected}
                      className="mt-1 block w-full text-sm text-gray-500 file:mr-3 file:rounded-md file:border-0 file:bg-blue-100 file:px-3 file:py-1.5 file:text-sm file:font-medium file:text-blue-700 hover:file:bg-blue-200"
                    />
                    {localAttachments.length > 0 && (
                      <ul className="mt-2 space-y-1">
                        {localAttachments.map((att, i) => (
                          <li key={i} className="flex items-center justify-between text-xs text-gray-600">
                            <span>{att.filename} ({att.content_type})</span>
                            <button
                              type="button"
                              onClick={() => setLocalAttachments((prev) => prev.filter((_, j) => j !== i))}
                              className="ml-2 text-red-400 hover:text-red-600"
                            >
                              ×
                            </button>
                          </li>
                        ))}
                      </ul>
                    )}
                  </div>
                  <button
                    type="button"
                    onClick={handleAddLocalStep}
                    disabled={!localContent.trim()}
                    className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-500 disabled:opacity-50"
                  >
                    Add to Steps
                  </button>
                </div>
              )}
            </div>
          </div>

          {/* Model & API Key Config */}
          <div className="rounded-xl bg-white p-6 shadow-sm ring-1 ring-gray-200">
            <h2 className="mb-4 text-base font-semibold text-gray-900">Execution Settings</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Default Model</label>
                <select
                  value={defaultModel}
                  onChange={(e) => setDefaultModel(e.target.value)}
                  className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                >
                  {MODELS.map((m) => (
                    <option key={m.value} value={m.value}>
                      {m.label} ({m.provider})
                    </option>
                  ))}
                </select>
              </div>

              <div className="flex items-center gap-3">
                <input
                  id="model-override"
                  type="checkbox"
                  checked={allowModelOverride}
                  onChange={(e) => setAllowModelOverride(e.target.checked)}
                  className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                <label htmlFor="model-override" className="text-sm text-gray-700">
                  Allow model override per step
                </label>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">API Key (for Run)</label>
                <select
                  value={selectedApiKeyId}
                  onChange={(e) => setSelectedApiKeyId(e.target.value)}
                  className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                >
                  {(apiKeys ?? []).map((k) => (
                    <option key={k.id} value={k.id}>
                      {k.provider} — {k.masked_key}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>
        </div>

        {/* Right: Version History */}
        <div className="rounded-xl bg-white p-6 shadow-sm ring-1 ring-gray-200">
          <h2 className="text-base font-semibold text-gray-900">Version History</h2>
          {isNew ? (
            <p className="mt-3 text-sm text-gray-500">Save your first version to see history here.</p>
          ) : (versions ?? []).length === 0 ? (
            <p className="mt-3 text-sm text-gray-500">No versions yet.</p>
          ) : (
            <ul className="mt-4 space-y-3">
              {(versions ?? []).map((v) => (
                <li key={v.id} className="rounded-lg border border-gray-100 p-3">
                  <div className="flex items-center justify-between">
                    <VersionTag version={v.version_number} />
                    <span className="text-xs text-gray-400">
                      {new Date(v.created_at).toLocaleDateString()}
                    </span>
                  </div>
                  <p className="mt-2 text-xs text-gray-500">
                    {v.steps.length} step(s) — {v.default_model}
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
