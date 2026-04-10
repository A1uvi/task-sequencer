import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useTaskExecution, useCancelTaskExecution } from '../hooks/useTaskExecutions'
import { useTaskVersion } from '../hooks/useTasks'
import { LoadingSpinner } from '../components/common/LoadingSpinner'
import { StatusBadge } from '../components/common/StatusBadge'

const TERMINAL_STATUSES = ['completed', 'failed', 'paused_exhausted']

export function TaskExecutionPage() {
  const { id } = useParams<{ id: string }>()
  const { data: execution, isLoading, error } = useTaskExecution(id ?? '')
  const { data: taskVersion } = useTaskVersion('', execution?.task_version_id ?? '')
  const cancelExecution = useCancelTaskExecution()
  const [expandedSteps, setExpandedSteps] = useState<Set<number>>(new Set())

  useEffect(() => {
    document.title = 'Task Execution — AI Workflow'
  }, [])

  const toggleStep = (index: number) => {
    setExpandedSteps((prev) => {
      const next = new Set(prev)
      if (next.has(index)) {
        next.delete(index)
      } else {
        next.add(index)
      }
      return next
    })
  }

  const handleCancel = async () => {
    if (!id) return
    await cancelExecution.mutateAsync(id)
  }

  if (isLoading) {
    return (
      <div className="flex h-full items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  if (error || !execution) {
    return (
      <div className="rounded-md bg-red-50 p-4 text-sm text-red-700">
        Failed to load execution. Please try again.
      </div>
    )
  }

  const totalSteps = taskVersion?.steps.length ?? 3
  const progressPercent =
    totalSteps > 0 ? (execution.current_step_index / totalSteps) * 100 : 0
  const isTerminal = TERMINAL_STATUSES.includes(execution.status)

  const stepOutputEntries = Object.entries(execution.step_outputs)

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Task Execution</h1>
          <p className="mt-1 text-sm text-gray-500">ID: {execution.id}</p>
        </div>
        <div className="flex items-center gap-3">
          <StatusBadge status={execution.status} />
          {!isTerminal && (
            <button
              type="button"
              onClick={handleCancel}
              disabled={cancelExecution.isPending}
              className="rounded-md border border-red-600 px-3 py-1.5 text-sm font-medium text-red-600 hover:bg-red-50 disabled:opacity-50"
            >
              Cancel
            </button>
          )}
        </div>
      </div>

      {/* Progress Bar */}
      <div className="rounded-xl bg-white p-6 shadow-sm ring-1 ring-gray-200">
        <div className="flex items-center justify-between text-sm text-gray-600">
          <span>
            Step {execution.current_step_index} of {totalSteps}
          </span>
          <span>{Math.round(progressPercent)}%</span>
        </div>
        <div className="mt-2 h-2 w-full overflow-hidden rounded-full bg-gray-200">
          <div
            className="h-full rounded-full bg-blue-600 transition-all duration-500"
            style={{ width: `${progressPercent}%` }}
          />
        </div>

        {execution.status === 'running' && !isTerminal && (
          <div className="mt-3 flex items-center gap-2 text-sm text-blue-600">
            <LoadingSpinner size="sm" />
            <span>Polling for updates every 3 seconds...</span>
          </div>
        )}

        {execution.status === 'paused_exhausted' && (
          <div className="mt-3 rounded-md bg-yellow-50 p-3 text-sm text-yellow-700">
            Execution paused: API key exhausted. Please add credits and resume.
          </div>
        )}

        {(execution.status === 'failed' || execution.status === 'paused_exhausted') &&
          execution.error_message && (
            <div className="mt-3 rounded-md bg-red-50 p-3 text-sm text-red-700">
              <strong>Error:</strong> {execution.error_message}
            </div>
          )}
      </div>

      {/* Execution Details */}
      <div className="rounded-xl bg-white p-6 shadow-sm ring-1 ring-gray-200">
        <h2 className="text-base font-semibold text-gray-900">Details</h2>
        <dl className="mt-4 grid grid-cols-2 gap-4 text-sm">
          <div>
            <dt className="text-gray-500">Status</dt>
            <dd className="mt-1"><StatusBadge status={execution.status} /></dd>
          </div>
          <div>
            <dt className="text-gray-500">Created</dt>
            <dd className="mt-1 text-gray-900">
              {new Date(execution.created_at).toLocaleString()}
            </dd>
          </div>
          <div>
            <dt className="text-gray-500">Task Version</dt>
            <dd className="mt-1 text-gray-900">{execution.task_version_id}</dd>
          </div>
          <div>
            <dt className="text-gray-500">Last Updated</dt>
            <dd className="mt-1 text-gray-900">
              {new Date(execution.updated_at).toLocaleString()}
            </dd>
          </div>
        </dl>
      </div>

      {/* Step Outputs Accordion */}
      <div className="rounded-xl bg-white shadow-sm ring-1 ring-gray-200">
        <div className="border-b border-gray-200 px-6 py-4">
          <h2 className="text-base font-semibold text-gray-900">Step Outputs</h2>
        </div>

        {stepOutputEntries.length === 0 ? (
          <div className="p-6 text-sm text-gray-500">
            No step outputs yet. Execution in progress...
          </div>
        ) : (
          <ul className="divide-y divide-gray-100">
            {stepOutputEntries.map(([stepIndex, output]) => {
              const idx = Number(stepIndex)
              const isExpanded = expandedSteps.has(idx)
              return (
                <li key={stepIndex}>
                  <button
                    type="button"
                    onClick={() => toggleStep(idx)}
                    className="flex w-full items-center justify-between px-6 py-4 text-left hover:bg-gray-50"
                  >
                    <span className="text-sm font-medium text-gray-900">
                      Step {idx + 1} Output
                    </span>
                    <svg
                      className={`h-4 w-4 text-gray-400 transition-transform ${isExpanded ? 'rotate-180' : ''}`}
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  </button>
                  {isExpanded && (
                    <div className="border-t border-gray-100 bg-gray-50 px-6 py-4">
                      <pre className="whitespace-pre-wrap text-sm text-gray-700">
                        {typeof output === 'string' ? output : JSON.stringify(output, null, 2)}
                      </pre>
                    </div>
                  )}
                </li>
              )
            })}
          </ul>
        )}
      </div>

      {execution.last_prompt_version_id && (
        <div className="text-sm text-gray-500">
          Last prompt:{' '}
          <Link
            to={`/prompts/${execution.last_prompt_version_id}`}
            className="text-blue-600 hover:text-blue-500"
          >
            {execution.last_prompt_version_id}
          </Link>
        </div>
      )}
    </div>
  )
}
