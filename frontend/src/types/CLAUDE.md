# src/types — TypeScript Interfaces

## Purpose
Single source of truth for all TypeScript types matching backend models.
Every component, hook, and API function imports types from here.

## Rules
- Never define model interfaces anywhere else in the codebase
- Enums must match backend values exactly (string enums)
- Keep in sync with `backend/app/schemas/`

## Adding a New Type
Add the interface to `index.ts`.
If it's a new model type, also add a corresponding API file in `src/api/`
and a hook in `src/hooks/`.
