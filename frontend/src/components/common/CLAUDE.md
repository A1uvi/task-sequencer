# src/components/common — Reusable UI Primitives

## Components
- `StatusBadge.tsx` — color-coded badge for TaskExecutionStatus and APIKeyStatus
- `VersionTag.tsx` — displays version number (e.g. "v3")
- `ProviderIcon.tsx` — icon for openai / claude / gemini
- `EmptyState.tsx` — empty list placeholder with optional CTA
- `LoadingSpinner.tsx` — centered spinner
- `ConfirmDialog.tsx` — modal for destructive actions (delete, revoke)

## Rules
- Accept data as props, never fetch internally
- Fully typed props interfaces
- Tested for renders and key interactions
