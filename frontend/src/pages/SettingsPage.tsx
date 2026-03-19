import { useEffect, useState } from 'react'
import { useCurrentUser, useUpdateNotificationPreferences } from '../hooks/useAuth'
import { LoadingSpinner } from '../components/common/LoadingSpinner'

interface NotificationPref {
  key: string
  label: string
  description: string
}

const NOTIFICATION_PREFS: NotificationPref[] = [
  {
    key: 'token_exhausted',
    label: 'Token Exhausted',
    description: 'Notify when an API key runs out of tokens.',
  },
  {
    key: 'token_refilled',
    label: 'Token Refilled',
    description: 'Notify when an API key token balance is refilled.',
  },
  {
    key: 'task_completed',
    label: 'Task Completed',
    description: 'Notify when a task execution completes successfully.',
  },
  {
    key: 'task_failed',
    label: 'Task Failed',
    description: 'Notify when a task execution fails.',
  },
]

export function SettingsPage() {
  const { data: user, isLoading } = useCurrentUser()
  const updatePrefs = useUpdateNotificationPreferences()

  const [prefs, setPrefs] = useState<Record<string, boolean>>({})
  const [saveSuccess, setSaveSuccess] = useState(false)
  const [saveError, setSaveError] = useState<string | null>(null)

  useEffect(() => {
    document.title = 'Settings — AI Workflow'
  }, [])

  useEffect(() => {
    if (user) {
      setPrefs(user.notification_preferences)
    }
  }, [user])

  const handleToggle = (key: string) => {
    setPrefs((prev) => ({ ...prev, [key]: !prev[key] }))
    setSaveSuccess(false)
  }

  const handleSave = async () => {
    setSaveError(null)
    setSaveSuccess(false)
    try {
      await updatePrefs.mutateAsync(prefs)
      setSaveSuccess(true)
      setTimeout(() => setSaveSuccess(false), 3000)
    } catch {
      setSaveError('Failed to save settings. Please try again.')
    }
  }

  if (isLoading) {
    return (
      <div className="flex h-full items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
        <p className="mt-1 text-sm text-gray-500">
          Manage your account preferences and notification settings.
        </p>
      </div>

      {/* Account Info */}
      <div className="rounded-xl bg-white p-6 shadow-sm ring-1 ring-gray-200">
        <h2 className="text-base font-semibold text-gray-900">Account</h2>
        <div className="mt-4">
          <p className="text-sm text-gray-500">Email</p>
          <p className="mt-1 text-sm font-medium text-gray-900">
            {user?.email ?? 'Loading...'}
          </p>
        </div>
      </div>

      {/* Notification Preferences */}
      <div className="rounded-xl bg-white p-6 shadow-sm ring-1 ring-gray-200">
        <h2 className="text-base font-semibold text-gray-900">
          Notification Preferences
        </h2>
        <p className="mt-1 text-sm text-gray-500">
          Choose which events trigger email notifications.
        </p>

        <div className="mt-6 space-y-4">
          {NOTIFICATION_PREFS.map((pref) => (
            <div
              key={pref.key}
              className="flex items-start justify-between gap-4 rounded-lg border border-gray-100 p-4"
            >
              <div className="flex-1">
                <p className="text-sm font-medium text-gray-900">{pref.label}</p>
                <p className="mt-0.5 text-sm text-gray-500">{pref.description}</p>
              </div>
              <button
                type="button"
                role="switch"
                aria-checked={prefs[pref.key] ?? false}
                onClick={() => handleToggle(pref.key)}
                className={`relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 ${
                  prefs[pref.key] ? 'bg-blue-600' : 'bg-gray-200'
                }`}
              >
                <span
                  className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${
                    prefs[pref.key] ? 'translate-x-5' : 'translate-x-0'
                  }`}
                />
              </button>
            </div>
          ))}
        </div>

        {saveError && (
          <div className="mt-4 rounded-md bg-red-50 p-3 text-sm text-red-700">
            {saveError}
          </div>
        )}

        {saveSuccess && (
          <div className="mt-4 rounded-md bg-green-50 p-3 text-sm text-green-700">
            Settings saved successfully.
          </div>
        )}

        <div className="mt-6 flex justify-end">
          <button
            type="button"
            onClick={handleSave}
            disabled={updatePrefs.isPending}
            className="flex items-center gap-2 rounded-md bg-blue-600 px-6 py-2.5 text-sm font-semibold text-white hover:bg-blue-500 disabled:opacity-50"
          >
            {updatePrefs.isPending && <LoadingSpinner size="sm" />}
            Save Settings
          </button>
        </div>
      </div>
    </div>
  )
}
