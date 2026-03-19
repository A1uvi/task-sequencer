# src/api — API Client and Request Functions

## Purpose
All HTTP communication with the backend lives here.
Components never call Axios directly — they use hooks from `src/hooks/`.

## Files
- `client.ts` — Axios instance: base URL, JWT interceptor, 401 redirect
- `auth.ts` — login, register
- `prompts.ts` — prompt + version CRUD
- `tasks.ts` — task + version CRUD
- `apiKeys.ts` — key management + sharing
- `taskExecutions.ts` — initiate + poll executions
- `conversations.ts` — read-only conversation fetch
- `folders.ts` — folder CRUD
- `search.ts` — search query

## Return Types
All functions must be fully typed using interfaces from `src/types/index.ts`.
Never use `any`.

## Error Handling
Let Axios errors propagate. TanStack Query handles them in hooks.
Only catch errors here if specific transformation is needed.
