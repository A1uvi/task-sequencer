import { useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { useConversation } from '../hooks/useConversations'
import { LoadingSpinner } from '../components/common/LoadingSpinner'
import { ProviderIcon } from '../components/common/ProviderIcon'

export function ConversationViewerPage() {
  const { id } = useParams<{ id: string }>()
  const { data: conversation, isLoading, error } = useConversation(id ?? '')

  useEffect(() => {
    document.title = 'Conversation — AI Workflow'
  }, [])

  if (isLoading) {
    return (
      <div className="flex h-full items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  if (error || !conversation) {
    return (
      <div className="rounded-md bg-red-50 p-4 text-sm text-red-700">
        Failed to load conversation. Please try again.
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Conversation</h1>
        <p className="mt-1 text-sm text-gray-500">
          {new Date(conversation.created_at).toLocaleString()}
        </p>
      </div>

      {/* Metadata */}
      <div className="rounded-xl bg-white p-6 shadow-sm ring-1 ring-gray-200">
        <h2 className="mb-4 text-base font-semibold text-gray-900">Details</h2>
        <div className="flex flex-wrap gap-4">
          <div>
            <span className="text-xs font-medium uppercase text-gray-500">Provider</span>
            <div className="mt-1">
              <ProviderIcon provider={conversation.provider} />
            </div>
          </div>
          <div>
            <span className="text-xs font-medium uppercase text-gray-500">Model</span>
            <p className="mt-1 text-sm font-medium text-gray-900">{conversation.model}</p>
          </div>
          <div>
            <span className="text-xs font-medium uppercase text-gray-500">Prompt Version</span>
            <p className="mt-1 text-sm text-gray-900">{conversation.prompt_version_id}</p>
          </div>
        </div>
      </div>

      {/* Token Usage */}
      <div className="rounded-xl bg-white p-6 shadow-sm ring-1 ring-gray-200">
        <h2 className="mb-4 text-base font-semibold text-gray-900">Token Usage</h2>
        <div className="grid grid-cols-3 gap-4 text-center">
          <div className="rounded-lg bg-gray-50 p-4">
            <p className="text-xs font-medium uppercase text-gray-500">Prompt Tokens</p>
            <p className="mt-2 text-2xl font-bold text-gray-900">
              {conversation.token_usage.prompt_tokens.toLocaleString()}
            </p>
          </div>
          <div className="rounded-lg bg-gray-50 p-4">
            <p className="text-xs font-medium uppercase text-gray-500">Completion Tokens</p>
            <p className="mt-2 text-2xl font-bold text-gray-900">
              {conversation.token_usage.completion_tokens.toLocaleString()}
            </p>
          </div>
          <div className="rounded-lg bg-blue-50 p-4">
            <p className="text-xs font-medium uppercase text-blue-600">Total Tokens</p>
            <p className="mt-2 text-2xl font-bold text-blue-700">
              {conversation.token_usage.total_tokens.toLocaleString()}
            </p>
          </div>
        </div>
      </div>

      {/* Message Thread */}
      <div className="rounded-xl bg-white shadow-sm ring-1 ring-gray-200">
        <div className="border-b border-gray-200 px-6 py-4">
          <h2 className="text-base font-semibold text-gray-900">
            Message Thread ({conversation.full_message_log.length} messages)
          </h2>
        </div>
        <div className="divide-y divide-gray-100">
          {conversation.full_message_log.map((message, index) => (
            <div
              key={index}
              className={`px-6 py-4 ${
                message.role === 'assistant' ? 'bg-blue-50' : 'bg-white'
              }`}
            >
              <div className="flex items-center gap-2">
                <span
                  className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-semibold capitalize ${
                    message.role === 'assistant'
                      ? 'bg-blue-100 text-blue-700'
                      : message.role === 'system'
                      ? 'bg-gray-100 text-gray-600'
                      : 'bg-green-100 text-green-700'
                  }`}
                >
                  {message.role}
                </span>
              </div>
              <div className="mt-2 text-sm text-gray-800 whitespace-pre-wrap">
                {message.content}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
