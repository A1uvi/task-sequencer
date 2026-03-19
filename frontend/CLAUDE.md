# Frontend

## Stack
React 18, TypeScript (strict), Vite, TanStack Query v5, React Router v6,
Axios, Tailwind CSS, Vitest, React Testing Library

## Structure
- `src/types/` — TypeScript interfaces matching all backend models
- `src/api/` — Axios API client and per-resource request functions
- `src/hooks/` — TanStack Query hooks (one per resource)
- `src/pages/` — Full page components (one per route)
- `src/components/layout/` — Sidebar, TopBar, Layout wrapper
- `src/components/common/` — Reusable UI components

## Running
```bash
npm run dev          # dev server
npm run build        # production build
npm run test         # Vitest
```

## API Integration
All API calls go through `src/api/client.ts` (Axios instance).
JWT token is attached automatically via request interceptor.
401 responses redirect to /login automatically.

## State Management
Server state: TanStack Query only. No Redux, no Zustand.
Local UI state: useState / useReducer inside components.

## Routing
All routes defined in `src/App.tsx`.
Protected routes use a `<ProtectedRoute>` wrapper that checks for a valid JWT.

## Types
`src/types/index.ts` is the single source of truth for all TypeScript interfaces.
These must stay in sync with the backend Pydantic schemas.
Never define model types inline in components.
