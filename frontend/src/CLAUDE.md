# frontend/src — React Application Source

## Entry Points
- `main.tsx` — React root mount with QueryClientProvider and RouterProvider
- `App.tsx` — Route definitions and ProtectedRoute wrapper

## Organization
- `types/` — TypeScript model interfaces (single source of truth)
- `api/` — Axios client + per-resource API functions
- `hooks/` — TanStack Query wrappers
- `pages/` — One component per route
- `components/layout/` — Shell UI (sidebar, topbar)
- `components/common/` — Shared primitives

## Import Order Convention
1. React imports
2. Third-party libraries
3. Internal: types, api, hooks, components
4. Styles (if any)
