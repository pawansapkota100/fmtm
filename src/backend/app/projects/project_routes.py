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
"""Endpoints for FMTM projects."""

import json
import os
import uuid
from io import BytesIO
from pathlib import Path
from typing import Optional

import geojson
import requests
from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    Response,
    UploadFile,
)
from fastapi.responses import FileResponse, JSONResponse
from loguru import logger as log
from osm_fieldwork.data_models import data_models_path
from osm_fieldwork.make_data_extract import getChoices
from osm_fieldwork.xlsforms import xlsforms_path
from sqlalchemy.orm import Session
from sqlalchemy.sql import text

from app.auth.osm import AuthUser, login_required
from app.auth.roles import mapper, org_admin, project_admin
from app.central import central_crud
from app.db import database, db_models
from app.db.postgis_utils import (
    check_crs,
    flatgeobuf_to_geojson,
    parse_and_filter_geojson,
)
from app.models.enums import TILES_FORMATS, TILES_SOURCE, HTTPStatus
from app.organisations import organisation_deps
from app.projects import project_crud, project_deps, project_schemas
from app.static import data_path
from app.submissions import submission_crud
from app.tasks import tasks_crud

router = APIRouter(
    prefix="/projects",
    tags=["projects"],
    responses={404: {"description": "Not found"}},
)


@router.get("/", response_model=list[project_schemas.ProjectOut])
async def read_projects(
    user_id: int = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(database.get_db),
):
    """Return all projects."""
    project_count, projects = await project_crud.get_projects(db, user_id, skip, limit)
    return projects


# TODO delete me
# @router.get("/details/{project_id}/")
# async def get_projet_details(
#     project_id: int,
#     db: Session = Depends(database.get_db),
#     current_user: AuthUser = Depends(mapper),
# ):
#     """Returns the project details.

#     Also includes ODK project details, so takes extra time to return.

#     Parameters:
#         project_id: int

#     Returns:
#         Response: Project details.
#     """
#     project = await project_crud.get_project(db, project_id)
#     if not project:
#         raise HTTPException(status_code=404, detail={"Project not found"})

#     # ODK Credentials
#     odk_credentials = project_schemas.ODKCentralDecrypted(
#         odk_central_url=project.odk_central_url,
#         odk_central_user=project.odk_central_user,
#         odk_central_password=project.odk_central_password,
#     )

#     odk_details = central_crud.get_odk_project_full_details(
#         project.odkid, odk_credentials
#     )

#     # Features count
#     query = text(
#         "select count(*) from features where "
#         f"project_id={project_id} and task_id is not null"
#     )
#     result = db.execute(query)
#     features = result.fetchone()[0]

#     return {
#         "id": project_id,
#         "odkName": odk_details["name"],
#         "createdAt": odk_details["createdAt"],
#         "tasks": odk_details["forms"],
#         "lastSubmission": odk_details["lastSubmission"],
#         "total_features": features,
#     }


@router.post("/near_me", response_model=list[project_schemas.ProjectSummary])
async def get_tasks_near_me(lat: float, long: float, user_id: int = None):
    """Get projects near me.

    TODO to be implemented in future.
    """
    return [project_schemas.ProjectSummary()]


@router.get("/summaries", response_model=project_schemas.PaginatedProjectSummaries)
async def read_project_summaries(
    user_id: int = None,
    hashtags: str = None,
    page: int = Query(1, ge=1),  # Default to page 1, must be greater than or equal to 1
    results_per_page: int = Query(13, le=100),
    db: Session = Depends(database.get_db),
):
    """Get a paginated summary of projects."""
    try:
        if hashtags:
            hashtags = hashtags.split(",")  # create list of hashtags
            hashtags = list(
                filter(lambda hashtag: hashtag.startswith("#"), hashtags)
            )  # filter hashtags that do start with #

        total_projects = db.query(db_models.DbProject).count()
        skip = (page - 1) * results_per_page
        limit = results_per_page

        project_count, projects = await project_crud.get_project_summaries(
            db, user_id, 
            skip, limit, hashtags, None
        )

        pagination = await project_crud.get_pagination(
            page, project_count, results_per_page, total_projects
        )
        project_summaries = [
            project_schemas.ProjectSummary.from_db_project(project) for project in projects
        ]

        response = project_schemas.PaginatedProjectSummaries(
            results=project_summaries,
            pagination=pagination,
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    

@router.get(
    "/search-projects", response_model=project_schemas.PaginatedProjectSummaries
)
async def search_project(
    search: str,
    user_id: int = None,
    hashtags: str = None,
    page: int = Query(1, ge=1),  # Default to page 1, must be greater than or equal to 1
    results_per_page: int = Query(13, le=100),
    db: Session = Depends(database.get_db),
):
    
    """Search projects by string, hashtag, or other criteria."""
    try:
        if hashtags:
            hashtags = hashtags.split(",")  # create list of hashtags
            hashtags = list(
                filter(lambda hashtag: hashtag.startswith("#"), hashtags)
            )  # filter hashtags that do start with #

        total_projects = db.query(db_models.DbProject).count()
        skip = (page - 1) * results_per_page
        limit = results_per_page

        project_count, projects = await project_crud.get_project_summaries(
            db, user_id, skip, limit, hashtags, search
        )

        pagination = await project_crud.get_pagination(
            page, project_count, results_per_page, total_projects
        )
        project_summaries = [
            project_schemas.ProjectSummary.from_db_project(project) for project in projects
        ]

        response = project_schemas.PaginatedProjectSummaries(
            results=project_summaries,
            pagination=pagination,
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/{project_id}", response_model=project_schemas.ReadProject)
async def read_project(project_id: int, db: Session = Depends(database.get_db)):
    """Get a specific project by ID."""
    project = await project_crud.get_project_by_id(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.delete("/{project_id}")
async def delete_project(
    db: Session = Depends(database.get_db),
    org_user_dict: db_models.DbUser = Depends(org_admin),
):
    """Delete a project from both ODK Central and the local database."""
    project = org_user_dict.get("project")

    log.info(
        f"User {org_user_dict.get('user').username} attempting "
        f"deletion of project {project.id}"
    )
    # Odk crendentials
    odk_credentials = await project_deps.get_odk_credentials(db, project.id)
    # Delete ODK Central project
    await central_crud.delete_odk_project(project.odkid, odk_credentials)
    # Delete FMTM project
    await project_crud.delete_one_project(db, project)

    log.info(f"Deletion of project {project.id} successful")
    return Response(status_code=HTTPStatus.NO_CONTENT)


@router.post("/create_project", response_model=project_schemas.ProjectOut)
async def create_project(
    project_info: project_schemas.ProjectUpload,
    org_user_dict: db_models.DbUser = Depends(org_admin),
    db: Session = Depends(database.get_db),
):
    """Create a project in ODK Central and the local database.

    The org_id and project_id params are inherited from the org_admin permission.
    Either param can be passed to determine if the user has admin permission
    to the organisation (or organisation associated with a project).

    TODO refactor to standard REST POST to /projects
    TODO but first check doesn't break other endpoints
    """
    db_user = org_user_dict.get("user")
    db_org = org_user_dict.get("org")
    project_info.organisation_id = db_org.id

    log.info(
        f"User {db_user.username} attempting creation of project "
        f"{project_info.project_info.name} in organisation ({db_org.id})"
    )

    # Must decrypt ODK password & connect to ODK Central before proj created
    # cannot use get_odk_credentials helper as no project id yet
    if project_info.odk_central_url:
        odk_creds_decrypted = project_schemas.ODKCentralDecrypted(
            odk_central_url=project_info.odk_central_url,
            odk_central_user=project_info.odk_central_user,
            odk_central_password=project_info.odk_central_password,
        )
    else:
        # Use default org credentials if none passed
        log.debug(
            "No odk credentials passed during project creation. "
            "Defaulting to organisation credentials."
        )
        odk_creds_decrypted = await organisation_deps.get_org_odk_creds(db_org)

    sql = text(
        """
            SELECT EXISTS (
                SELECT 1
                FROM project_info
                WHERE LOWER(name) = :project_name
            )
            """
    )
    result = db.execute(sql, {"project_name": project_info.project_info.name.lower()})
    project_exists = result.fetchone()[0]
    if project_exists:
        raise HTTPException(
            status_code=400,
            detail=f"Project already exists with the name "
            f"{project_info.project_info.name}",
        )

    odkproject = central_crud.create_odk_project(
        project_info.project_info.name,
        odk_creds_decrypted,
    )

    project = await project_crud.create_project_with_project_info(
        db,
        project_info,
        odkproject["id"],
        db_user,
    )
    if not project:
        raise HTTPException(status_code=404, detail="Project creation failed")

    return project


@router.put("/{project_id}", response_model=project_schemas.ProjectOut)
async def update_project(
    project_info: project_schemas.ProjectUpdate,
    db: Session = Depends(database.get_db),
    project_user_dict: dict = Depends(project_admin),
):
    """Update an existing project by ID.

    Note: the entire project JSON must be uploaded.
    If a partial update is required, use the PATCH method instead.

    Parameters:
    - id: ID of the project to update
    - project_info: Updated project information
    - current_user (DbUser): Check if user is project_admin

    Returns:
    - Updated project information

    Raises:
    - HTTPException with 404 status code if project not found
    """
    project = await project_crud.update_project_info(
        db, project_info, project_user_dict["project"], project_user_dict["user"]
    )
    if not project:
        raise HTTPException(status_code=422, detail="Project could not be updated")
    return project


@router.patch("/{project_id}", response_model=project_schemas.ProjectOut)
async def project_partial_update(
    project_id: int,
    project_info: project_schemas.ProjectPartialUpdate,
    db: Session = Depends(database.get_db),
    project_user_dict: dict = Depends(project_admin),
):
    """Partial Update an existing project by ID.

    Parameters:
    - id
    - name
    - short_description
    - description

    Returns:
    - Updated project information

    Raises:
    - HTTPException with 404 status code if project not found
    """
    # Update project informations
    project = await project_crud.partial_update_project_info(
        db, project_info, project_user_dict["project"]
    )

    if not project:
        raise HTTPException(status_code=422, detail="Project could not be updated")
    return project


@router.post("/{project_id}/upload-task-boundaries")
async def upload_project_task_boundaries(
    project_id: int,
    task_geojson: UploadFile = File(...),
    db: Session = Depends(database.get_db),
    org_user_dict: db_models.DbUser = Depends(org_admin),
):
    """Set project task boundaries using split GeoJSON from frontend.

    Each polygon in the uploaded geojson are made into single task.

    Required Parameters:
        project_id (id): ID for associated project.
        task_geojson (UploadFile): Multi-polygon GeoJSON file.

    Returns:
        dict: JSON containing success message, project ID, and number of tasks.
    """
    log.debug(f"Uploading project boundary multipolygon for project ID: {project_id}")
    # read entire file
    content = await task_geojson.read()
    task_boundaries = json.loads(content)

    # Validatiing Coordinate Reference System
    await check_crs(task_boundaries)

    log.debug("Creating tasks for each polygon in project")
    await project_crud.create_tasks_from_geojson(db, project_id, task_boundaries)

    # Get the number of tasks in a project
    task_count = await tasks_crud.get_task_count_in_project(db, project_id)

    return {
        "message": "Project Boundary Uploaded",
        "project_id": f"{project_id}",
        "task_count": task_count,
    }


@router.post("/task-split")
async def task_split(
    project_geojson: UploadFile = File(...),
    extract_geojson: Optional[UploadFile] = File(None),
    no_of_buildings: int = Form(50),
    db: Session = Depends(database.get_db),
):
    """Split a task into subtasks.

    Args:
        project_geojson (UploadFile): The geojson to split.
            Should be a FeatureCollection.
        extract_geojson (UploadFile, optional): Custom data extract geojson
            containing osm features (should be a FeatureCollection).
            If not included, an extract is generated automatically.
        no_of_buildings (int, optional): The number of buildings per subtask.
            Defaults to 50.
        db (Session, optional): The database session. Injected by FastAPI.

    Returns:
        The result of splitting the task into subtasks.

    """
    # read project boundary
    parsed_boundary = geojson.loads(await project_geojson.read())
    # Validatiing Coordinate Reference Systems
    await check_crs(parsed_boundary)

    # read data extract
    parsed_extract = None
    if extract_geojson:
        geojson_data = await extract_geojson.read()
        parsed_extract = parse_and_filter_geojson(geojson_data, filter=False)
        if parsed_extract:
            await check_crs(parsed_extract)
        else:
            log.warning("Parsed geojson file contained no geometries")

    return await project_crud.split_geojson_into_tasks(
        db,
        parsed_boundary,
        no_of_buildings,
        parsed_extract,
    )


@router.post("/edit_project_boundary/{project_id}/")
async def edit_project_boundary(
    project_id: int,
    boundary_geojson: UploadFile = File(...),
    dimension: int = Form(500),
    db: Session = Depends(database.get_db),
    project_user_dict: dict = Depends(project_admin),
):
    """Edit the existing project boundary."""
    # Validating for .geojson File.
    file_name = os.path.splitext(boundary_geojson.filename)
    file_ext = file_name[1]
    allowed_extensions = [".geojson", ".json"]
    if file_ext not in allowed_extensions:
        raise HTTPException(status_code=400, detail="Provide a valid .geojson file")

    # read entire file
    content = await boundary_geojson.read()
    boundary = json.loads(content)

    # Validatiing Coordinate Reference System
    await check_crs(boundary)

    result = await project_crud.update_project_boundary(
        db, project_id, boundary, dimension
    )
    if not result:
        raise HTTPException(
            status_code=428, detail=f"Project with id {project_id} does not exist"
        )

    # Get the number of tasks in a project
    task_count = await tasks_crud.get_task_count_in_project(db, project_id)

    return {
        "message": "Project Boundary Uploaded",
        "project_id": project_id,
        "task_count": task_count,
    }


@router.post("/validate-form")
async def validate_form(form: UploadFile):
    """Tests the validity of the xls form uploaded.

    Parameters:
        - form: The xls form to validate
    """
    file = Path(form.filename)
    file_ext = file.suffix.lower()

    allowed_extensions = [".xls", ".xlsx", ".xml"]
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400, detail="Provide a valid .xls,.xlsx,.xml file"
        )

    contents = await form.read()
    return await central_crud.read_and_test_xform(BytesIO(contents), file_ext)


@router.post("/{project_id}/generate-project-data")
async def generate_files(
    background_tasks: BackgroundTasks,
    project_id: int,
    xls_form_upload: Optional[UploadFile] = File(None),
    db: Session = Depends(database.get_db),
    org_user_dict: db_models.DbUser = Depends(org_admin),
):
    """Generate additional content to initialise the project.

    Boundary, ODK Central forms, QR codes, etc.

    Accepts a project ID, category, custom form flag, and an uploaded file as inputs.
    The generated files are associated with the project ID and stored in the database.
    This api generates odk appuser tokens, forms. This api also creates an app user for
    each task and provides the required roles.
    Some of the other functionality of this api includes converting a xls file
    provided by the user to the xform, generates osm data extracts and uploads
    it to the form.

    Args:
        background_tasks (BackgroundTasks): FastAPI bg tasks, provided automatically.
        project_id (int): The ID of the project for which files are being generated.
        xls_form_upload (UploadFile, optional): A custom XLSForm to use in the project.
            A file should be provided if user wants to upload a custom xls form.
        db (Session): Database session, provided automatically.
        org_user_dict (AuthUser): Current logged in user. Must be org admin.

    Returns:
        json (JSONResponse): A success message containing the project ID.
    """
    log.debug(f"Generating media files tasks for project: {project_id}")

    project = org_user_dict.get("project")

    xform_category = project.xform_category
    custom_xls_form = None
    file_ext = None
    if xls_form_upload:
        log.debug("Validating uploaded XLS form")

        file_path = Path(xls_form_upload.filename)
        file_ext = file_path.suffix.lower()
        allowed_extensions = {".xls", ".xlsx", ".xml"}
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
                detail=f"Invalid file extension, must be {allowed_extensions}",
            )

        custom_xls_form = await xls_form_upload.read()

        # Write XLS form content to db
        project.form_xls = custom_xls_form
        db.commit()

    # Create task in db and return uuid
    log.debug(f"Creating export background task for project ID: {project_id}")
    background_task_id = await project_crud.insert_background_task_into_database(
        db, project_id=str(project_id)
    )

    log.debug(f"Submitting {background_task_id} to background tasks stack")
    background_tasks.add_task(
        project_crud.generate_project_files,
        db,
        project_id,
        BytesIO(custom_xls_form) if custom_xls_form else None,
        xform_category,
        file_ext if xls_form_upload else ".xls",
        background_task_id,
    )

    return JSONResponse(
        status_code=200,
        content={"Message": f"{project_id}", "task_id": f"{background_task_id}"},
    )


@router.get("/generate-log/")
async def generate_log(
    project_id: int,
    uuid: uuid.UUID,
    db: Session = Depends(database.get_db),
    org_user_dict: db_models.DbUser = Depends(org_admin),
):
    r"""Get the contents of a log file in a log format.

    ### Response
    - **200 OK**: Returns the contents of the log file in a log format.
        Each line is separated by a newline character "\n".

    - **500 Internal Server Error**: Returns an error message if the log file
        cannot be generated.

    ### Return format
    Task Status and Logs are returned in a JSON format.
    """
    try:
        # Get the backgrund task status
        task_status, task_message = await project_crud.get_background_task_status(
            uuid, db
        )

        sql = text(
            """
            SELECT
                COUNT(CASE WHEN odk_token IS NOT NULL THEN 1 END) AS tasks_complete,
                COUNT(*) AS total_tasks
            FROM tasks
            WHERE project_id = :project_id;
        """
        )
        result = db.execute(sql, {"project_id": project_id})
        row = result.fetchone()

        tasks_generated = row[0] if row else 0
        total_task_count = row[1] if row else 0

        project_log_file = Path("/opt/logs/create_project.json")
        project_log_file.touch(exist_ok=True)
        with open(project_log_file, "r") as log_file:
            logs = [json.loads(line) for line in log_file]

            filtered_logs = [
                log.get("record", {}).get("message", None)
                for log in logs
                if log.get("record", {}).get("extra", {}).get("project_id")
                == project_id
            ]
            last_50_logs = filtered_logs[-50:]

            logs = "\n".join(last_50_logs)

            return {
                "status": task_status.name,
                "total_tasks": total_task_count,
                "message": task_message,
                "progress": tasks_generated,
                "logs": logs,
            }
    except Exception as e:
        log.error(e)
        return "Error in generating log file"


@router.get("/categories/")
async def get_categories(current_user: AuthUser = Depends(login_required)):
    """Get api for fetching all the categories.

    This endpoint fetches all the categories from osm_fieldwork.

    ## Response
    - Returns a JSON object containing a list of categories and their respoective forms.

    """
    try:
        # FIXME update to use osm-rawdata
        categories = (
            getChoices()
    )  # categories are fetched from osm_fieldwork.make_data_extracts.getChoices()
        return categories
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/preview-split-by-square/")
async def preview_split_by_square(
    project_geojson: UploadFile = File(...), dimension: int = Form(100)
):
    """Preview splitting by square.

    TODO update to use a response_model
    """
    # Validating for .geojson File.
    file_name = os.path.splitext(project_geojson.filename)
    file_ext = file_name[1]
    allowed_extensions = [".geojson", ".json"]
    if file_ext not in allowed_extensions:
        raise HTTPException(status_code=400, detail="Provide a valid .geojson file")

    # read entire file
    content = await project_geojson.read()
    boundary = geojson.loads(content)

    # Validatiing Coordinate Reference System
    await check_crs(boundary)

    result = await project_crud.preview_split_by_square(boundary, dimension)
    return result


@router.post("/generate-data-extract/")
async def get_data_extract(
    geojson_file: UploadFile = File(...),
    form_category: Optional[str] = Form(None),
    # config_file: Optional[str] = Form(None),
    current_user: AuthUser = Depends(login_required),
):
    """Get a new data extract for a given project AOI.

    TODO allow config file (YAML/JSON) upload for data extract generation
    TODO alternatively, direct to raw-data-api to generate first, then upload
    """
    boundary_geojson = json.loads(await geojson_file.read())

    # Get extract config file from existing data_models
    if form_category:
        data_model = f"{data_models_path}/{form_category}.yaml"
        with open(data_model, "rb") as data_model_yaml:
            extract_config = BytesIO(data_model_yaml.read())
    else:
        extract_config = None

    fgb_url = await project_crud.generate_data_extract(
        boundary_geojson,
        extract_config,
    )

    return JSONResponse(status_code=200, content={"url": fgb_url})


@router.get("/data-extract-url/")
async def get_or_set_data_extract(
    url: Optional[str] = None,
    project_id: int = Query(..., description="Project ID"),
    db: Session = Depends(database.get_db),
    project_user_dict: dict = Depends(project_admin),
):
    try:
        """Get or set the data extract URL for a project."""
        fgb_url = await project_crud.get_or_set_data_extract_url(
            db,
            project_id,
            url,
        )
        return JSONResponse(status_code=200, content={"url": fgb_url})
    except Exception as e:
        raise HTTPException(status_code=400, detail="fail to extract data from url {e}") from e

@router.post("/upload-custom-extract/")
async def upload_custom_extract(
    custom_extract_file: UploadFile = File(...),
    project_id: int = Query(..., description="Project ID"),
    db: Session = Depends(database.get_db),
    project_user_dict: dict = Depends(project_admin),
):
    """Upload a custom data extract geojson for a project.

    Extract can be in geojson for flatgeobuf format.

    Note the following properties are mandatory:
    - "id"
    - "osm_id"
    - "tags"
    - "version"
    - "changeset"
    - "timestamp"

    Extracts are best generated with https://export.hotosm.org for full compatibility.

    Request Body
    - 'custom_extract_file' (file): File with the data extract features.

    Query Params:
    - 'project_id' (int): the project's id. Required.
    """
    # Validating for .geojson File.
    file_name = os.path.splitext(custom_extract_file.filename)
    file_ext = file_name[1]
    allowed_extensions = [".geojson", ".json", ".fgb"]
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400, detail="Provide a valid .geojson or .fgb file"
        )

    # read entire file
    extract_data = await custom_extract_file.read()

    if file_ext == ".fgb":
        fgb_url = await project_crud.upload_custom_fgb_extract(
            db, project_id, extract_data
        )
    else:
        fgb_url = await project_crud.upload_custom_geojson_extract(
            db, project_id, extract_data
        )
    return JSONResponse(status_code=200, content={"url": fgb_url})


@router.get("/download-form/{project_id}/")
async def download_form(
    project_id: int,
    db: Session = Depends(database.get_db),
    current_user: AuthUser = Depends(login_required),
):
    """Download the XLSForm for a project."""
    try:
        project = await project_crud.get_project(db, project_id)

        headers = {
            "Content-Disposition": "attachment; filename=submission_data.xls",
            "Content-Type": "application/media",
        }
        if not project.form_xls:
            xlsform_path = f"{xlsforms_path}/{project.xform_category}.xls"
            if os.path.exists(xlsform_path):
                return FileResponse(xlsform_path, filename="form.xls")
            else:
                raise HTTPException(status_code=404, detail="Form not found")
        return Response(content=project.form_xls, headers=headers)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/update-form")
async def update_project_form(
    background_tasks: BackgroundTasks,
    category: str = Form(...),
    upload: Optional[UploadFile] = File(None),
    db: Session = Depends(database.get_db),
    project_user_dict: dict = Depends(project_admin),
) -> project_schemas.ProjectBase:
    """Update the XForm data in ODK Central.

    Also updates the category and custom XLSForm data in the database.
    """
    # TODO migrate most logic to project_crud
    project = project_user_dict["project"]

    if project.xform_category == category:
        if not upload:
            raise HTTPException(
                status_code=400, detail="Current category is same as new category"
            )

    if upload:
        file_ext = Path(upload.filename).suffix.lower()
        allowed_extensions = [".xls", ".xlsx", ".xml"]
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
                detail="Provide a valid .xls, .xlsx, .xml file.",
            )
        new_xform_data = await upload.read()
        # Update the XLSForm blob in the database
        project.form_xls = new_xform_data
        new_xform_data = BytesIO(new_xform_data)
    else:
        xlsform_path = Path(f"{xlsforms_path}/{category}.xls")
        file_ext = xlsform_path.suffix.lower()
        with open(xlsform_path, "rb") as f:
            new_xform_data = BytesIO(f.read())

    # Update form category in database
    project.xform_category = category
    # Commit changes to db
    db.commit()

    # The reference to the form via ODK Central API (minus task_id)
    xform_name_prefix = project.project_name_prefix

    # Get ODK Central credentials for project
    odk_creds = await project_deps.get_odk_credentials(db, project.id)
    # Get task id list
    task_list = await tasks_crud.get_task_id_list(db, project.id)
    # Update ODK Central form data
    # FIXME runs in background but status is not tracked
    background_tasks.add_task(
        central_crud.update_odk_xforms,
        task_list,
        project.odkid,
        new_xform_data,
        file_ext,
        xform_name_prefix,
        odk_creds,
    )

    return project


@router.get("/download_template/")
async def download_template(
    category: str,
    db: Session = Depends(database.get_db),
    current_user: AuthUser = Depends(mapper),
):
    """Download an XLSForm template to fill out."""
    xlsform_path = f"{xlsforms_path}/{category}.xls"
    if os.path.exists(xlsform_path):
        return FileResponse(xlsform_path, filename="form.xls")
    else:
        raise HTTPException(status_code=404, detail="Form not found")


@router.get("/{project_id}/download")
async def download_project_boundary(
    project_id: int,
    db: Session = Depends(database.get_db),
    current_user: AuthUser = Depends(mapper),
):
    """Downloads the boundary of a project as a GeoJSON file.

    Args:
        project_id (int): The id of the project.
        db (Session): The database session, provided automatically.
        current_user (AuthUser): Check if user is mapper.

    Returns:
        Response: The HTTP response object containing the downloaded file.
    """
    try:
        out = await project_crud.get_project_geometry(db, project_id)
        headers = {
            "Content-Disposition": "attachment; filename=project_outline.geojson",
            "Content-Type": "application/media",
        }

        return Response(content=out, headers=headers)
    except Exception as e:
        raise HTTPException(status_code=400, detail="Fail to download project boundary: " + str(e)) from e


@router.get("/{project_id}/download_tasks")
async def download_task_boundaries(
    project_id: int,
    db: Session = Depends(database.get_db),
    current_user: Session = Depends(mapper),
):
    """Downloads the boundary of the tasks for a project as a GeoJSON file.

    Args:
        project_id (int): The id of the project.
        db (Session): The database session, provided automatically.
        current_user (AuthUser): Check if user has MAPPER permission.

    Returns:
        Response: The HTTP response object containing the downloaded file.
    """
    try:
        out = await project_crud.get_task_geometry(db, project_id)

        headers = {
            "Content-Disposition": "attachment; filename=project_outline.geojson",
            "Content-Type": "application/media",
        }

        return Response(content=out, headers=headers)
    except Exception as e:
        raise HTTPException(status_code=400, detail="Fail to download project boundary: " + str(e)) from e


@router.get("/features/download/")
async def download_features(
    project_id: int,
    task_id: Optional[int] = None,
    db: Session = Depends(database.get_db),
    current_user: AuthUser = Depends(mapper),
):
    """Downloads the features of a project as a GeoJSON file.

    Can generate a geojson for the entire project, or specific task areas.

    Args:
        project_id (int): The id of the project.
        task_id (int): Specify a specific task area to download for.
        db (Session): The database session, provided automatically.
        current_user (AuthUser): Check if user has MAPPER permission.

    Returns:
        Response: The HTTP response object containing the downloaded file.
    """
    try:
        feature_collection = await project_crud.get_project_features_geojson(
            db, project_id, task_id
        )
        headers = {
            "Content-Disposition": (
                f"attachment; filename=fmtm_project_{project_id}_features.geojson"
            ),
            "Content-Type": "application/media",
        }
        return Response(content=json.dumps(feature_collection), headers=headers)
    
    except Exception as e:
        raise HTTPException(status_code=400, detail="fail to download features:" + str(e)) from e


@router.get("/convert-fgb-to-geojson/")
async def convert_fgb_to_geojson(
    url: str,
    db: Session = Depends(database.get_db),
    current_user: AuthUser = Depends(login_required),
):
    """Convert flatgeobuf to GeoJSON format, extracting GeometryCollection.

    Helper endpoint to test data extracts during project creation.
    Required as the flatgeobuf files wrapped in GeometryCollection
    cannot be read in QGIS or other tools.

    Args:
        url (str): URL to the flatgeobuf file.
        db (Session): The database session, provided automatically.
        current_user (AuthUser): Check if user is logged in.

    Returns:
        Response: The HTTP response object containing the downloaded file.
    """
    try:
        with requests.get(url) as response:
            if not response.ok:
                raise HTTPException(
                    status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
                    detail="Download failed for data extract",
                )
            data_extract_geojson = await flatgeobuf_to_geojson(db, response.content)

        if not data_extract_geojson:
            raise HTTPException(
                status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
                detail=("Failed to convert flatgeobuf --> geojson"),
            )

        headers = {
            "Content-Disposition": ("attachment; filename=fmtm_data_extract.geojson"),
            "Content-Type": "application/media",
        }

        return Response(content=json.dumps(data_extract_geojson), headers=headers)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/tiles/{project_id}")
async def generate_project_tiles(
    background_tasks: BackgroundTasks,
    project_id: int,
    source: str = Query(
        ..., description="Select a source for tiles", enum=TILES_SOURCE
    ),
    format: str = Query(
        "mbtiles", description="Select an output format", enum=TILES_FORMATS
    ),
    tms: str = Query(
        None,
        description="Provide a custom TMS URL, optional",
    ),
    db: Session = Depends(database.get_db),
    current_user: AuthUser = Depends(mapper),
):
    """Returns basemap tiles for a project.

    Args:
        background_tasks (BackgroundTasks): FastAPI bg tasks, provided automatically.
        project_id (int): ID of project to create tiles for.
        source (str): Tile source ("esri", "bing", "topo", "google", "oam").
        format (str, optional): Default "mbtiles". Other options: "pmtiles", "sqlite3".
        tms (str, optional): Default None. Custom TMS provider URL.
        db (Session): The database session, provided automatically.
        current_user (AuthUser): Check if user has MAPPER permission.

    Returns:
        str: Success message that tile generation started.
    """
    try:
    # Create task in db and return uuid
        log.debug(
            "Creating generate_project_tiles background task "
            f"for project ID: {project_id}"
        )
        background_task_id = await project_crud.insert_background_task_into_database(
            db, project_id=project_id
        )
        background_tasks.add_task(
            project_crud.get_project_tiles,
            db,
            project_id,
            background_task_id,
            source,
            format,
            tms,
        )
        return {"Message": "Tile generation started"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/tiles_list/{project_id}/")
async def tiles_list(
    project_id: int,
    db: Session = Depends(database.get_db),
    current_user: AuthUser = Depends(login_required),
):
    """Returns the list of tiles for a project.

    Parameters:
        project_id: int
        db (Session): The database session, provided automatically.
        current_user (AuthUser): Check if user is logged in.

    Returns:
        Response: List of generated tiles for a project.
    """
    return await project_crud.get_mbtiles_list(db, project_id)

@router.get("/download_tiles/")
async def download_tiles(
    tile_id: int,
    db: Session = Depends(database.get_db),
    current_user: AuthUser = Depends(login_required),
):
    try:
        """Download the basemap tile archive for a project."""
        log.debug("Getting tile archive path from DB")
        tiles_path = (
            db.query(db_models.DbTilesPath)
            .filter(db_models.DbTilesPath.id == str(tile_id))
            .first()
            )
        log.info(f"User requested download for tiles: {tiles_path.path}")
        project_id = tiles_path.project_id
        project = await project_crud.get_project(db, project_id)
        filename = Path(tiles_path.path).name.replace(
            f"{project_id}_", f"{project.project_name_prefix}_"
        )
        log.debug(f"Sending tile archive to user: {filename}")

        return FileResponse(
            tiles_path.path,
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

@router.get("/boundary_in_osm/{project_id}/")
async def download_task_boundary_osm(
    project_id: int,
    db: Session = Depends(database.get_db),
    current_user: AuthUser = Depends(mapper),
):
    """Downloads the boundary of a task as a OSM file.

        Args:
            project_id (int): The id of the project.
            db (Session): The database session, provided automatically.
            current_user (AuthUser): Check if user has MAPPER permission.

        Returns:
            Response: The HTTP response object containing the downloaded file.
        """
    try:
        out = await project_crud.get_task_geometry(db, project_id)
        file_path = f"/tmp/{project_id}_task_boundary.geojson"

        # Write the response content to the file
        with open(file_path, "w") as f:
            f.write(out)
        result = await project_crud.convert_geojson_to_osm(file_path)

        with open(result, "r") as f:
            content = f.read()

        response = Response(content=content, media_type="application/xml")
        return response
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/centroid/")
async def project_centroid(
    project_id: int = None,
    db: Session = Depends(database.get_db),
):
    """Get a centroid of each projects.

    Parameters:
        project_id (int): The ID of the project.
        db (Session): The database session, provided automatically.

    Returns:
        list[tuple[int, str]]: A list of tuples containing the task ID and
            the centroid as a string.
    """
    try:
        query = text(
            f"""SELECT id,
                ARRAY_AGG(ARRAY[ST_X(ST_Centroid(outline)),
                ST_Y(ST_Centroid(outline))]) AS centroid
                FROM projects
                WHERE {f"id={project_id}" if project_id else "1=1"}
                GROUP BY id;"""
        )

        result = db.execute(query)
        result_dict_list = [{"id": row[0], "centroid": row[1]} for row in result.fetchall()]
        return result_dict_list
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
        

@router.get("/task-status/{uuid}", response_model=project_schemas.BackgroundTaskStatus)
async def get_task_status(
    task_uuid: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(database.get_db),
):
    """Get the background task status by passing the task UUID."""
    # Get the backgrund task status
    try:
        task_status, task_message = await project_crud.get_background_task_status(
            task_uuid, db
        )
        return project_schemas.BackgroundTaskStatus(
            status=task_status.name,
            message=task_message or None,
            # progress=some_func_to_get_progress,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/templates/") # TODO
async def get_template_file(
    file_type: str = Query(
        ..., enum=["data_extracts", "form"], description="Choose file type"
    ),
    current_user: AuthUser = Depends(login_required),
):
    """Get template file.

    Args: file_type: Type of template file.

    returns: Requested file as a FileResponse.
    """
    try:
        file_type_paths = {
            "data_extracts": f"{data_path}/template/template.geojson",
            "form": f"{data_path}/template/template.xls",
        }
        file_path = file_type_paths.get(file_type)
        filename = file_path.split("/")[-1]
        return FileResponse(
            file_path, media_type="application/octet-stream", filename=filename)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Template not found {str(e)}") from e



@router.get(
    "/project_dashboard/{project_id}", response_model=project_schemas.ProjectDashboard
)
async def project_dashboard(
    background_tasks: BackgroundTasks,
    db_project: db_models.DbProject = Depends(project_deps.get_project_by_id),
    db_organisation: db_models.DbOrganisation = Depends(
        organisation_deps.org_from_project
    ),
    db: Session = Depends(database.get_db),
):
    """Get the project dashboard details.

    Args:
        background_tasks (BackgroundTasks): FastAPI bg tasks, provided automatically.
        db_project (db_models.DbProject): An instance of the project.
        db_organisation (db_models.DbOrganisation): An instance of the organisation.
        db (Session): The database session.

    Returns:
        ProjectDashboard: The project dashboard details.
    """
    try:
        data = await project_crud.get_dashboard_detail(db_project, db_organisation, db)

        background_task_id = await project_crud.insert_background_task_into_database(
            db, "sync_submission", db_project.id
        )
        # Update submissions in S3
        background_tasks.add_task(
            submission_crud.update_submission_in_s3, db, db_project.id, background_task_id
        )

        return data
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/contributors/{project_id}")
async def get_contributors(
    project_id: int,
    db: Session = Depends(database.get_db),
    current_user: AuthUser = Depends(mapper),
):
    """Get contributors of a project.

    Args:
        project_id (int): ID of project.
        db (Session): The database session.
        current_user (AuthUser): Check if user is mapper.

    Returns:
        list[project_schemas.ProjectUser]: List of project users.
    """
    project_users = await project_crud.get_project_users(db, project_id)
    return project_users


@router.post("/add_admin/")
async def add_new_project_admin(
    db: Session = Depends(database.get_db),
    project_user_dict: dict = Depends(project_admin),
):
    """Add a new project manager.

    The logged in user must be either the admin of the organisation or a super admin.
    """
    return await project_crud.add_project_admin(
        db, project_user_dict["user"], project_user_dict["project"]
    )
