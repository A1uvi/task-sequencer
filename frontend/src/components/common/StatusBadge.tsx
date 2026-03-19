import { TaskExecutionStatus, APIKeyStatus } from '../../types'

interface Props {
  status: TaskExecutionStatus | APIKeyStatus
}

const statusConfig: Record<string, { label: string; classes: string }> = {
  // TaskExecutionStatus
  queued: { label: 'Queued', classes: 'bg-gray-100 text-gray-700' },
  running: { label: 'Running', classes: 'bg-blue-100 text-blue-700' },
  paused_exhausted: {
    label: 'Paused (Exhausted)',
    classes: 'bg-yellow-100 text-yellow-700',
  },
  completed: { label: 'Completed', classes: 'bg-green-100 text-green-700' },
  failed: { label: 'Failed', classes: 'bg-red-100 text-red-700' },
  // APIKeyStatus
  active: { label: 'Active', classes: 'bg-green-100 text-green-700' },
  exhausted: { label: 'Exhausted', classes: 'bg-yellow-100 text-yellow-700' },
  revoked: { label: 'Revoked', classes: 'bg-red-100 text-red-700' },
}

export function StatusBadge({ status }: Props) {
  const config = statusConfig[status] ?? {
    label: status,
    classes: 'bg-gray-100 text-gray-700',
  }

  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${config.classes}`}
    >
      {config.label}
    </span>
  )
}
