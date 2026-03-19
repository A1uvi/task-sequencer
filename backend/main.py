from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import auth, folders, prompts, tasks, api_keys, task_executions, conversations, search

app = FastAPI(title="AI Workflow Platform")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(folders.router, prefix="/folders", tags=["folders"])
app.include_router(prompts.router, prefix="/prompts", tags=["prompts"])
app.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
app.include_router(api_keys.router, prefix="/api-keys", tags=["api-keys"])
app.include_router(task_executions.router, prefix="/task-executions", tags=["task-executions"])
app.include_router(conversations.router, prefix="/conversations", tags=["conversations"])
app.include_router(search.router, prefix="/search", tags=["search"])
