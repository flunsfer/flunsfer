from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import Task, User
from app.schemas import TaskCreate, TaskOut, TaskUpdate

router = APIRouter(prefix="/tasks", tags=["tasks"])


def _get_owned_task(task_id: int, user: User, db: Session) -> Task:
    task = db.execute(
        select(Task).where(Task.id == task_id, Task.owner_id == user.id)
    ).scalar_one_or_none()
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return task


@router.get("", response_model=list[TaskOut])
def list_tasks(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[Task]:
    return list(db.execute(select(Task).where(Task.owner_id == user.id)).scalars())


@router.post("", response_model=TaskOut, status_code=status.HTTP_201_CREATED)
def create_task(
    payload: TaskCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Task:
    task = Task(title=payload.title, description=payload.description, owner_id=user.id)
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.get("/{task_id}", response_model=TaskOut)
def get_task(
    task_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> Task:
    return _get_owned_task(task_id, user, db)


@router.patch("/{task_id}", response_model=TaskOut)
def update_task(
    task_id: int,
    payload: TaskUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Task:
    task = _get_owned_task(task_id, user, db)
    if payload.title is not None:
        task.title = payload.title
    if payload.description is not None:
        task.description = payload.description
    if payload.done is not None:
        task.done = payload.done
    db.commit()
    db.refresh(task)
    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> None:
    task = _get_owned_task(task_id, user, db)
    db.delete(task)
    db.commit()
