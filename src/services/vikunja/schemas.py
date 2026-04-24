from pydantic import BaseModel


class VikunjaProject(BaseModel):
    id: int
    title: str
    description: str = ""
    is_archived: bool = False


class VikunjaTask(BaseModel):
    id: int
    title: str
    description: str = ""
    done: bool = False
    project_id: int
    due_date: str | None = None


class CreateTaskRequest(BaseModel):
    title: str
    project_id: int
    description: str = ""
    due_date: str | None = None


class UpdateTaskRequest(BaseModel):
    title: str | None = None
    description: str | None = None
    done: bool | None = None
    due_date: str | None = None
