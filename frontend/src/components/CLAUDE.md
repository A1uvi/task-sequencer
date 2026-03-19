# src/components — Shared UI Components

## layout/
- `Layout.tsx` — wraps pages with Sidebar + TopBar
- `Sidebar.tsx` — nav links to all pages
- `TopBar.tsx` — current user, logout, search shortcut

## common/
- `StatusBadge.tsx` — color-coded badge for TaskExecutionStatus and APIKeyStatus
- `VersionTag.tsx` — displays version number (e.g. "v3")
- `ProviderIcon.tsx` — icon for openai / claude / gemini
- `EmptyState.tsx` — empty list placeholder with optional CTA
- `LoadingSpinner.tsx` — centered spinner
- `ConfirmDialog.tsx` — modal for destructive actions (delete, revoke)

## Rules
- All components must be fully typed with explicit props interfaces
- No component fetches data directly — accept data as props
- All components must be tested (renders + key interactions)
