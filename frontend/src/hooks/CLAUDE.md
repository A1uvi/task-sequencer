# src/hooks — TanStack Query Hooks

## Purpose
Wrap all API calls in TanStack Query. Components use these hooks,
never the `src/api/` functions directly.

## Pattern
```typescript
export function usePrompts(folderId?: string) {
  return useQuery({
    queryKey: ['prompts', folderId],
    queryFn: () => api.prompts.list(folderId),
  });
}
```

## Polling
TaskExecution hooks must poll while status is `queued` or `running`:
```typescript
refetchInterval: (data) =>
  data?.status === 'queued' || data?.status === 'running' ? 3000 : false,
```

## Mutations
Use `useMutation` for all writes. Call `queryClient.invalidateQueries`
on success to keep list views in sync.
