import { useEffect } from 'react'
import { Link } from 'react-router-dom'
import { usePrompts } from '../hooks/usePrompts'
import { useTasks } from '../hooks/useTasks'
import { useTaskExecutions } from '../hooks/useTaskExecutions'
import { LoadingSpinner } from '../components/common/LoadingSpinner'
import { StatusBadge } from '../components/common/StatusBadge'
import { VersionTag } from '../components/common/VersionTag'

export function DashboardPage() {
  const { data: promptsData, isLoading: promptsLoading } = usePrompts()
  const { data: tasksData, isLoading: tasksLoading } = useTasks()
  const { data: executionsData, isLoading: executionsLoading } = useTaskExecutions()

  useEffect(() => {
    document.title = 'Dashboard — AI Workflow'
  }, [])

  const recentPrompts = (promptsData?.items ?? []).slice(0, 5)
  const recentTasks = (tasksData?.items ?? []).slice(0, 5)
  const recentExecutions = (executionsData?.items ?? []).slice(0, 3)

  const statsCards = [
    {
      label: 'Total Prompts',
      value: promptsData?.total ?? 0,
      href: '/prompts',
      color: 'bg-blue-50 text-blue-700',
    },
    {
      label: 'Total Tasks',
      value: tasksData?.total ?? 0,
      href: '/tasks',
      color: 'bg-purple-50 text-purple-700',
    },
    {
      label: 'Total Executions',
      value: executionsData?.total ?? 0,
      href: '/tasks',
      color: 'bg-green-50 text-green-700',
    },
  ]

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="mt-1 text-sm text-gray-500">
          Welcome back. Here is an overview of your workspace.
        </p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        {statsCards.map((card) => (
          <Link
            key={card.label}
            to={card.href}
            className="rounded-xl bg-white p-6 shadow-sm ring-1 ring-gray-200 hover:shadow-md transition-shadow"
          >
            <p className="text-sm font-medium text-gray-500">{card.label}</p>
            <p className={`mt-2 text-3xl font-bold ${card.color.split(' ')[1]}`}>
              {card.value}
            </p>
          </Link>
        ))}
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Recent Prompts */}
        <div className="rounded-xl bg-white p-6 shadow-sm ring-1 ring-gray-200">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-semibold text-gray-900">Recent Prompts</h2>
            <Link
              to="/prompts"
              className="text-sm font-medium text-blue-600 hover:text-blue-500"
            >
              View all
            </Link>
          </div>

          {promptsLoading ? (
            <LoadingSpinner className="mt-6" />
          ) : recentPrompts.length === 0 ? (
            <p className="mt-4 text-sm text-gray-500">No prompts yet.</p>
          ) : (
            <ul className="mt-4 divide-y divide-gray-100">
              {recentPrompts.map((prompt) => (
                <li key={prompt.id}>
                  <Link
                    to={`/prompts/${prompt.id}`}
                    className="flex items-center justify-between py-3 hover:bg-gray-50 -mx-2 px-2 rounded-lg"
                  >
                    <span className="text-sm font-medium text-gray-900">
                      {prompt.title}
                    </span>
                    <span className="text-xs text-gray-400 capitalize">
                      {prompt.visibility_type}
                    </span>
                  </Link>
                </li>
              ))}
            </ul>
          )}

          <Link
            to="/prompts/new"
            className="mt-4 flex w-full items-center justify-center rounded-md border border-blue-600 px-4 py-2 text-sm font-medium text-blue-600 hover:bg-blue-50"
          >
            New Prompt
          </Link>
        </div>

        {/* Recent Tasks */}
        <div className="rounded-xl bg-white p-6 shadow-sm ring-1 ring-gray-200">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-semibold text-gray-900">Recent Tasks</h2>
            <Link
              to="/tasks"
              className="text-sm font-medium text-blue-600 hover:text-blue-500"
            >
              View all
            </Link>
          </div>

          {tasksLoading ? (
            <LoadingSpinner className="mt-6" />
          ) : recentTasks.length === 0 ? (
            <p className="mt-4 text-sm text-gray-500">No tasks yet.</p>
          ) : (
            <ul className="mt-4 divide-y divide-gray-100">
              {recentTasks.map((task) => (
                <li key={task.id}>
                  <Link
                    to={`/tasks/${task.id}`}
                    className="flex items-center justify-between py-3 hover:bg-gray-50 -mx-2 px-2 rounded-lg"
                  >
                    <span className="text-sm font-medium text-gray-900">
                      {task.title}
                    </span>
                    <span className="text-xs text-gray-400 capitalize">
                      {task.visibility_type}
                    </span>
                  </Link>
                </li>
              ))}
            </ul>
          )}

          <Link
            to="/tasks"
            className="mt-4 flex w-full items-center justify-center rounded-md border border-purple-600 px-4 py-2 text-sm font-medium text-purple-600 hover:bg-purple-50"
          >
            New Task
          </Link>
        </div>
      </div>

      {/* Recent Executions */}
      <div className="rounded-xl bg-white p-6 shadow-sm ring-1 ring-gray-200">
        <h2 className="text-base font-semibold text-gray-900">Recent Executions</h2>

        {executionsLoading ? (
          <LoadingSpinner className="mt-6" />
        ) : recentExecutions.length === 0 ? (
          <p className="mt-4 text-sm text-gray-500">No executions yet.</p>
        ) : (
          <ul className="mt-4 divide-y divide-gray-100">
            {recentExecutions.map((execution) => (
              <li key={execution.id}>
                <Link
                  to={`/executions/${execution.id}`}
                  className="flex items-center justify-between py-3 hover:bg-gray-50 -mx-2 px-2 rounded-lg"
                >
                  <div className="flex items-center gap-3">
                    <StatusBadge status={execution.status} />
                    <span className="text-sm text-gray-600">
                      Task version: <VersionTag version={1} />
                    </span>
                  </div>
                  <span className="text-xs text-gray-400">
                    {new Date(execution.created_at).toLocaleDateString()}
                  </span>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  )
}
