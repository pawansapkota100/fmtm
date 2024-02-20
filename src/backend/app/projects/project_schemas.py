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
"""Pydantic schemas for Projects."""

import uuid
from datetime import datetime
from typing import Any, List, Optional, Union

from dateutil import parser
from geojson_pydantic import Feature, FeatureCollection, Polygon
from loguru import logger as log
from pydantic import BaseModel, Field, computed_field
from pydantic.functional_serializers import field_serializer
from pydantic.functional_validators import field_validator, model_validator
from typing_extensions import Self

from app.config import HttpUrlStr, decrypt_value, encrypt_value
from app.db import db_models
from app.db.postgis_utils import (
    geojson_to_geometry,
    geometry_to_geojson,
    get_address_from_lat_lon,
    read_wkb,
    write_wkb,
)
from app.models.enums import ProjectPriority, ProjectStatus, TaskSplitType
from app.tasks import tasks_schemas
from app.users.user_schemas import User


class ODKCentralIn(BaseModel):
    """ODK Central credentials inserted to database."""

    odk_central_url: Optional[HttpUrlStr] = None
    odk_central_user: Optional[str] = None
    odk_central_password: Optional[str] = None

    @field_validator("odk_central_url", mode="after")
    @classmethod
    def remove_trailing_slash(cls, value: HttpUrlStr) -> Optional[HttpUrlStr]:
        """Remove trailing slash from ODK Central URL."""
        if not value:
            return None
        if value.endswith("/"):
            return value[:-1]
        return value

    @model_validator(mode="after")
    def all_odk_vars_together(self) -> Self:
        """Ensure if one ODK variable is set, then all are."""
        if any(
            [
                self.odk_central_url,
                self.odk_central_user,
                self.odk_central_password,
            ]
        ) and not all(
            [
                self.odk_central_url,
                self.odk_central_user,
                self.odk_central_password,
            ]
        ):
            err = "All ODK details are required together: url, user, password"
            log.debug(err)
            raise ValueError(err)
        return self

    @field_validator("odk_central_password", mode="after")
    @classmethod
    def encrypt_odk_password(cls, value: str) -> Optional[str]:
        """Encrypt the ODK Central password before db insertion."""
        if not value:
            return None
        return encrypt_value(value)


class ODKCentralDecrypted(BaseModel):
    """ODK Central credentials extracted from database.

    WARNING never return this as a response model.
    WARNING or log to the terminal.
    """

    odk_central_url: Optional[HttpUrlStr] = None
    odk_central_user: Optional[str] = None
    odk_central_password: Optional[str] = None

    def model_post_init(self, ctx):
        """Run logic after model object instantiated."""
        # Decrypt odk central password from database
        if self.odk_central_password:
            if isinstance(self.odk_central_password, str):
                password = self.odk_central_password
            else:
                password = self.odk_central_password
            self.odk_central_password = decrypt_value(password)

    @field_validator("odk_central_url", mode="after")
    @classmethod
    def remove_trailing_slash(cls, value: HttpUrlStr) -> HttpUrlStr:
        """Remove trailing slash from ODK Central URL."""
        if not value:
            return ""
        if value.endswith("/"):
            return value[:-1]
        return value


class ProjectInfo(BaseModel):
    """Basic project info."""

    name: str
    short_description: str
    description: str
    per_task_instructions: Optional[str] = None


class ProjectIn(BaseModel):
    """Upload new project."""

    project_info: ProjectInfo
    xform_title: str
    organisation_id: Optional[int] = None
    hashtags: Optional[List[str]] = None
    task_split_type: Optional[TaskSplitType] = None
    task_split_dimension: Optional[int] = None
    task_num_buildings: Optional[int] = None
    data_extract_type: Optional[str] = None
    outline_geojson: Union[FeatureCollection, Feature, Polygon]
    # city: str
    # country: str

    @computed_field
    @property
    def outline(self) -> Optional[Any]:
        """Compute WKBElement geom from geojson."""
        if not self.outline_geojson:
            return None
        return geojson_to_geometry(self.outline_geojson)

    @computed_field
    @property
    def centroid(self) -> Optional[Any]:
        """Compute centroid for project outline."""
        if not self.outline:
            return None
        return write_wkb(read_wkb(self.outline).centroid)

    @computed_field
    @property
    def location_str(self) -> Optional[str]:
        """Compute geocoded location string from centroid."""
        if not self.centroid:
            return None
        geom = read_wkb(self.centroid)
        latitude, longitude = geom.y, geom.x
        address = get_address_from_lat_lon(latitude, longitude)
        return address if address is not None else ""

    @field_validator("hashtags", mode="after")
    @classmethod
    def prepend_hash_to_tags(cls, hashtags: List[str]) -> Optional[List[str]]:
        """Add '#' to hashtag if missing. Also added default '#FMTM'."""
        if not hashtags:
            return None

        hashtags_with_hash = [
            f"#{hashtag}" if hashtag and not hashtag.startswith("#") else hashtag
            for hashtag in hashtags
        ]

        if "#FMTM" not in hashtags_with_hash:
            hashtags_with_hash.append("#FMTM")

        return hashtags_with_hash


class ProjectUpload(ProjectIn, ODKCentralIn):
    """Project upload details, plus ODK credentials."""

    pass


class ProjectPartialUpdate(BaseModel):
    """Update projects metadata."""

    name: Optional[str] = None
    short_description: Optional[str] = None
    description: Optional[str] = None
    hashtags: Optional[List[str]] = None
    per_task_instructions: Optional[str] = None


class ProjectUpdate(ProjectIn):
    """Update project."""

    pass


class GeojsonFeature(BaseModel):
    """Features used for Task definitions."""

    id: int
    geometry: Optional[Feature] = None


class ProjectSummary(BaseModel):
    """Project summaries."""

    id: int = -1
    priority: ProjectPriority = ProjectPriority.MEDIUM
    priority_str: str = priority.name
    title: Optional[str] = None
    location_str: Optional[str] = None
    description: Optional[str] = None
    total_tasks: Optional[int] = None
    tasks_mapped: Optional[int] = None
    num_contributors: Optional[int] = None
    tasks_validated: Optional[int] = None
    tasks_bad: Optional[int] = None
    hashtags: Optional[List[str]] = None
    organisation_id: Optional[int] = None
    organisation_logo: Optional[str] = None

    @classmethod
    def from_db_project(
        cls,
        project: db_models.DbProject,
    ) -> "ProjectSummary":
        """Generate model from database obj."""
        priority = project.priority
        return cls(
            id=project.id,
            priority=priority,
            priority_str=priority.name,
            title=project.title,
            location_str=project.location_str,
            description=project.description,
            total_tasks=project.total_tasks,
            tasks_mapped=project.tasks_mapped,
            num_contributors=project.num_contributors,
            tasks_validated=project.tasks_validated,
            tasks_bad=project.tasks_bad,
            hashtags=project.hashtags,
            organisation_id=project.organisation_id,
            organisation_logo=project.organisation_logo,
        )


class PaginationInfo(BaseModel):
    """Pagination JSON return."""

    has_next: bool
    has_prev: bool
    next_num: Optional[int]
    page: int
    pages: int
    prev_num: Optional[int]
    per_page: int
    total: int


class PaginatedProjectSummaries(BaseModel):
    """Project summaries + Pagination info."""

    results: List[ProjectSummary]
    pagination: PaginationInfo


class ProjectBase(BaseModel):
    """Base project model."""

    outline: Any = Field(exclude=True)

    id: int
    odkid: int
    author: User
    project_info: ProjectInfo
    status: ProjectStatus
    # location_str: str
    project_tasks: Optional[List[tasks_schemas.Task]]
    xform_title: Optional[str] = None
    hashtags: Optional[List[str]] = None
    organisation_id: Optional[int] = None

    @computed_field
    @property
    def outline_geojson(self) -> Optional[Feature]:
        """Compute the geojson outline from WKBElement outline."""
        if not self.outline:
            return None
        return geometry_to_geojson(self.outline, {"id": self.id}, self.id)


class ProjectOut(ProjectBase):
    """Project display to user."""

    project_uuid: uuid.UUID = uuid.uuid4()


class ReadProject(ProjectBase):
    """Redundant model for refactor."""

    project_uuid: uuid.UUID = uuid.uuid4()
    location_str: Optional[str] = None
    data_extract_url: str


class BackgroundTaskStatus(BaseModel):
    """Background task status for project related tasks."""

    status: str
    message: Optional[str] = None


class ProjectDashboard(BaseModel):
    """Project details dashboard."""

    project_name_prefix: str
    organisation_name: str
    total_tasks: int
    created: datetime
    organisation_logo: Optional[str] = None
    total_submission: Optional[int] = None
    total_contributors: Optional[int] = None
    last_active: Optional[Union[str, datetime]] = None

    @field_serializer("last_active")
    def get_last_active(self, value, values):
        """Date of last activity on project."""
        if value is None:
            return None

        last_active = parser.parse(value).replace(tzinfo=None)
        current_date = datetime.now()

        time_difference = current_date - last_active

        days_difference = time_difference.days

        if days_difference == 0:
            return "today"
        elif days_difference == 1:
            return "yesterday"
        elif days_difference < 7:
            return f'{days_difference} day{"s" if days_difference > 1 else ""} ago'
        else:
            return last_active.strftime("%d %b %Y")
