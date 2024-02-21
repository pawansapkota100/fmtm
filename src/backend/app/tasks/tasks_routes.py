# Copyright (c) 2022, 2023 Humanitarian OpenStreetMap Team
#
# This file is part of FMTM.
#
#     FMTM is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     FMTM is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with FMTM.  If not, see <https:#www.gnu.org/licenses/>.
#
"""Routes for FMTM tasks."""

import json
from datetime import datetime, timedelta
from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session
from sqlalchemy.sql import text

from app.auth.osm import AuthUser, login_required
from app.auth.roles import get_uid, mapper, project_admin
from app.central import central_crud
from app.db import database
from app.models.enums import TaskStatus
from app.projects import project_crud, project_deps
from app.tasks import tasks_crud, tasks_schemas

router = APIRouter(
    prefix="/tasks",
    tags=["tasks"],
    responses={404: {"description": "Not found"}},
)


@router.get("/task-list", response_model=List[tasks_schemas.ReadTask])
async def read_task_list(
    project_id: int,
    limit: int = 1000,
    db: Session = Depends(database.get_db),
):
    """Get the task list for a project."""
    tasks = await tasks_crud.get_tasks(db, project_id, limit)
    updated_tasks = await tasks_crud.update_task_history(tasks, db)
    if not tasks:
        raise HTTPException(status_code=404, detail="Tasks not found")
    return updated_tasks


@router.get("/", response_model=List[tasks_schemas.Task])
async def read_tasks(
    project_id: int,
    user_id: int = None,
    skip: int = 0,
    limit: int = 1000,
    db: Session = Depends(database.get_db),
):
    """Get all task details, either for a project or user."""
    if user_id:
        raise HTTPException(
            status_code=300,
            detail="Please provide either user_id OR task_id, not both.",
        )

    tasks = await tasks_crud.get_tasks(db, project_id, user_id, skip, limit)
    if not tasks:
        raise HTTPException(status_code=404, detail="Tasks not found")
    return tasks


@router.get("/point_on_surface")
async def get_point_on_surface(project_id: int, db: Session = Depends(database.get_db)):
    """Get a point on the surface of the geometry for each task of the project.

    Parameters:
        project_id (int): The ID of the project.

    Returns:
        List[Tuple[int, str]]: A list of tuples containing the task ID
            and the centroid as a string.
    """
    query = text(
        f"""
            SELECT id,
            ARRAY_AGG(ARRAY[ST_X(ST_PointOnSurface(outline)),
            ST_Y(ST_PointOnSurface(outline))]) AS point
            FROM tasks
            WHERE project_id = {project_id}
            GROUP BY id; """
    )

    result = db.execute(query)
    result_dict_list = [{"id": row[0], "point": row[1]} for row in result.fetchall()]
    return result_dict_list


@router.post("/near_me", response_model=tasks_schemas.Task)
async def get_tasks_near_me(
    lat: float, long: float, project_id: int = None, user_id: int = None
):
    """Get tasks near the requesting user."""
    return "Coming..."


@router.get("/{task_id}", response_model=tasks_schemas.Task)
async def get_specific_task(task_id: int, db: Session = Depends(database.get_db)):
    """Get a specific task by it's ID."""
    task = await tasks_crud.get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.post(
    "/{task_id}/new_status/{new_status}", response_model=tasks_schemas.ReadTask
)
async def update_task_status(
    task_id: int,
    new_status: TaskStatus,
    db: Session = Depends(database.get_db),
    current_user: AuthUser = Depends(mapper),
):
    """Update the task status."""
    user_id = await get_uid(current_user)
    task = await tasks_crud.update_task_status(db, user_id, task_id, new_status)
    updated_task = await tasks_crud.update_task_history(task, db)
    if not task:
        raise HTTPException(status_code=404, detail="Task status could not be updated.")
    return updated_task


@router.post("/edit-task-boundary")
async def edit_task_boundary(
    task_id: int,
    boundary: UploadFile = File(...),
    db: Session = Depends(database.get_db),
    current_user: AuthUser = Depends(project_admin),
):
    """Update the task boundary manually."""
    # read entire file
    content = await boundary.read()
    boundary_json = json.loads(content)

    edit_boundary = await tasks_crud.edit_task_boundary(db, task_id, boundary_json)

    return edit_boundary


@router.get("/tasks-features/")
async def task_features_count(
    project_id: int,
    db: Session = Depends(database.get_db),
):
    """Get all features within a task area."""
    # Get the project object.
    project = await project_crud.get_project(db, project_id)

    # ODK Credentials
    odk_credentials = await project_deps.get_odk_credentials(project_id, db)

    odk_details = central_crud.list_odk_xforms(project.odkid, odk_credentials, True)

    # Assemble the final data list
    data = []
    for x in odk_details:
        feature_count_query = text(
            f"""
            select count(*) from features
            where project_id = {project_id} and task_id = {x['xmlFormId']}
        """
        )

        result = db.execute(feature_count_query)
        feature_count = result.fetchone()

        data.append(
            {
                "task_id": x["xmlFormId"],
                "submission_count": x["submissions"],
                "last_submission": x["lastSubmission"],
                "feature_count": feature_count[0],
            }
        )

    return data


@router.get("/task-comments/", response_model=list[tasks_schemas.TaskCommentResponse])
async def task_comments(
    project_id: int,
    task_id: int,
    db: Session = Depends(database.get_db),
):
    """Retrieve a list of task comments for a specific project and task.

    Args:
        project_id (int): The ID of the project.
        task_id (int): The ID of the task.
        db (Session, optional): The database session.

    Returns:
        List[tasks_schemas.TaskCommentResponse]: A list of task comments.
    """
    task_comment_list = await tasks_crud.get_task_comments(db, project_id, task_id)

    return task_comment_list


@router.post("/task-comments/", response_model=tasks_schemas.TaskCommentResponse)
async def add_task_comments(
    comment: tasks_schemas.TaskCommentRequest,
    db: Session = Depends(database.get_db),
    user_data: AuthUser = Depends(login_required),
):
    """Create a new task comment.

    Parameters:
        comment (TaskCommentRequest): The task comment to be created.
        db (Session): The database session.
        user_data (AuthUser): The authenticated user.

    Returns:
        TaskCommentResponse: The created task comment.
    """
    task_comment_list = await tasks_crud.add_task_comments(db, comment, user_data)
    return task_comment_list


@router.get("/activity/", response_model=List[tasks_schemas.TaskHistoryCount])
async def task_activity(
    project_id: int, days: int = 10, db: Session = Depends(database.get_db)
):
    """Retrieves the validate and mapped task count for a specific project.

    Args:
        project_id (int): The ID of the project.
        days (int): The number of days to consider for the
            task activity (default: 10).
        db (Session): The database session.

    Returns:
        list[TaskHistoryCount]: A list of task history counts.

    """
    end_date = datetime.now() - timedelta(days=days)
    task_history = await tasks_crud.get_project_task_history(project_id, end_date, db)

    return await tasks_crud.count_validated_and_mapped_tasks(
        task_history,
        end_date,
    )


@router.get("/task_history/", response_model=List[tasks_schemas.TaskHistory])
async def task_history(
    project_id: int, days: int = 10, db: Session = Depends(database.get_db)
):
    """Get the detailed task history for a project.

    Args:
        project_id (int): The ID of the project.
        days (int): The number of days to consider for the
            task activity (default: 10).
        db (Session): The database session.

    Returns:
        List[TaskHistory]: A list of task history.
    """
    end_date = datetime.now() - timedelta(days=days)
    return await tasks_crud.get_project_task_history(project_id, end_date, db)
