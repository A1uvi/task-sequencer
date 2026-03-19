import uuid
from dataclasses import dataclass


@dataclass
class ExecuteTaskStepJob:
    task_execution_id: uuid.UUID
    step_index: int
    api_key_id: uuid.UUID
