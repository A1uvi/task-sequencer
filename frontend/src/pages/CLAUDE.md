# src/pages — Page Components

## Purpose
Top-level route components. One file per route.

## Pages
- `LoginPage.tsx` — email/password login form
- `DashboardPage.tsx` — recent prompts, tasks, activity summary
- `PromptsPage.tsx` — list prompts with folder filter and search
- `PromptEditorPage.tsx` — create/edit prompt, version history, run button
- `TaskBuilderPage.tsx` — build task from prompt steps, model config, run button
- `TaskExecutionPage.tsx` — live polling monitor for a running task execution
- `ConversationViewerPage.tsx` — read-only message log with token usage
- `APIKeysPage.tsx` — manage keys: add, mask, share, revoke
- `SearchPage.tsx` — full-text search results across all resource types
- `SettingsPage.tsx` — notification preference toggles

## Rules
- Pages use hooks from `src/hooks/`, never `src/api/` directly
- Every page handles loading state, error state, and empty state explicitly
- No inline styles — Tailwind classes only
- Pages are responsible for their own `<title>` via a `useEffect`

## Adding a New Page
1. Create the component here
2. Register the route in `src/App.tsx`
3. Add a nav link in `src/components/layout/Sidebar.tsx`
4. Write a smoke test: renders without crashing
