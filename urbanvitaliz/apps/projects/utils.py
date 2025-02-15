# encoding: utf-8

"""
Utilities for projects

authors: raphael.marvie@beta.gouv.fr,guillaume.libersat@beta.gouv.fr
created: <2021-09-13 lun. 15:38>

"""

import uuid

from django.core.exceptions import PermissionDenied
from django.db.models import Q

from . import models


def can_administrate_project(project, user, allow_draft=False):
    """Check if user is allowed to administrate this project"""
    if user.is_anonymous:
        return False

    if is_member(user, project, allow_draft):
        return True

    if user.has_perm("projects.can_administrate_project") and in_allowed_departments(
        user, project
    ):
        return True

    return False


def is_member(user, project, allow_draft):
    """return true if user is member of the project"""
    return ((user.email == project.email) or (user.email in project.emails)) and (
        (not project.is_draft) or allow_draft
    )  # noqa: F841


def in_allowed_departments(user, project):
    """return true if project is in allowed departments for user"""
    allowed = user.profile.departments.values_list("code", flat=True)
    if not allowed:  # empty list means full access
        return True
    return project.commune and (project.commune.department_id in allowed)


def can_administrate_or_403(project, user, allow_draft=False):
    """Raise a 403 error is user is not a owner or admin"""
    if can_administrate_project(project, user, allow_draft=allow_draft):
        return True

    raise PermissionDenied("L'information demandée n'est pas disponible")


def generate_ro_key():
    """Generate the ReadOnly key for sharing"""
    return uuid.uuid4().hex


def get_active_project_id(request):
    """Return the active project ID for a given user"""
    return request.session.get("active_project", None)


def get_active_project(request):
    """Return the active project for a given user"""
    if not request.user.is_authenticated:
        return None

    project_id = get_active_project_id(request)
    project = None

    if project_id:
        try:
            project = models.Project.objects.get(id=project_id)
        except models.Project.DoesNotExist:
            pass
    else:
        try:
            project = models.Project.objects.filter(
                Q(email=request.user.email)
                | Q(is_draft=False, emails__contains=request.user.email)
            ).first()
        except models.Project.DoesNotExist:
            pass

    return project


def set_active_project_id(request, project_id: int):
    """Set the current project in a session cookie"""
    request.session["active_project"] = project_id


def refresh_user_projects_in_session(request, user):
    """store the user projects in the session"""
    projects = models.Project.objects.filter(
        Q(email=user.email) | Q(is_draft=False, emails__contains=user.email)
    )

    request.session["projects"] = list(
        {
            "name": p.name,
            "id": p.id,
            "location": p.location,
            "actions_open": p.tasks.open().count(),
        }
        for p in projects
    )
