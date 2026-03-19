// Enums
export type VisibilityType = 'private' | 'team' | 'public'
export type APIKeyOwnerType = 'user' | 'team'
export type APIKeyStatus = 'active' | 'exhausted' | 'revoked'
export type TaskExecutionStatus = 'queued' | 'running' | 'paused_exhausted' | 'completed' | 'failed'

// Models
export interface User {
  id: string
  email: string
  notification_preferences: Record<string, boolean>
  created_at: string
}

export interface Team {
  id: string
  name: string
  created_by: string
  created_at: string
}

export interface TeamMember {
  team_id: string
  user_id: string
  role: string
}

export interface Folder {
  id: string
  name: string
  visibility_type: VisibilityType
  team_ids: string[]
  created_by: string
  created_at: string
  updated_at: string
}

export interface Prompt {
  id: string
  title: string
  folder_id: string | null
  visibility_type: VisibilityType
  created_by: string
  current_version_id: string | null
  created_at: string
  updated_at: string
}

export interface PromptVersion {
  id: string
  prompt_id: string
  content: string
  usage_notes: string | null
  variables: Record<string, unknown>
  example_input: string | null
  example_output: string | null
  meta_notes: string | null
  tags: string[]
  version_number: number
  created_by: string
  created_at: string
}

export interface Conversation {
  id: string
  prompt_version_id: string
  provider: string
  model: string
  api_key_id: string
  full_message_log: Array<{ role: string; content: string }>
  token_usage: { prompt_tokens: number; completion_tokens: number; total_tokens: number }
  created_at: string
}

export interface APIKey {
  id: string
  provider: string
  masked_key: string // last 4 chars only — never the real key
  owner_type: APIKeyOwnerType
  owner_id: string
  shared_with_users: string[]
  shared_with_teams: string[]
  status: APIKeyStatus
  created_at: string
}

export interface Task {
  id: string
  title: string
  folder_id: string | null
  visibility_type: VisibilityType
  created_by: string
  current_version_id: string | null
  created_at: string
  updated_at: string
}

export interface TaskVersion {
  id: string
  task_id: string
  ordered_prompt_version_ids: string[]
  default_model: string
  allow_model_override_per_step: boolean
  version_number: number
  created_at: string
}

export interface TaskExecution {
  id: string
  task_version_id: string
  api_key_id: string
  status: TaskExecutionStatus
  current_step_index: number
  last_prompt_version_id: string | null
  step_outputs: Record<string, unknown>
  created_by: string
  created_at: string
  updated_at: string
}

// Auth
export interface AuthTokens {
  access_token: string
  token_type: string
}

// Search
export interface SearchResult {
  type: 'prompt' | 'task' | 'conversation'
  id: string
  title: string
  snippet: string
  created_at: string
}

// Pagination
export interface PaginatedResponse<T> {
  items: T[]
  total: number
  limit: number
  offset: number
}
