# encoding: utf-8

"""
Urls for projects application

author  : raphael.marvie@beta.gouv.fr,guillaume.libersat@beta.gouv.fr
created : 2021-05-26 15:54:25 CEST
"""


from django.urls import path

from . import views

urlpatterns = [
    path(r"onboarding/", views.onboarding, name="projects-onboarding"),
    path(
        r"login_redirect/",
        views.redirect_user_to_project,
        name="projects-redirect-user-to-project",
    ),
    # projects for switchtenders
    path(r"projects/", views.project_list, name="projects-project-list"),
    path("projects/feed/", views.LatestProjectsFeed(), name="projects-feed"),
    path(
        r"project/<int:project_id>/",
        views.project_detail,
        name="projects-project-detail",
    ),
    path(
        r"project/<int:project_id>/update/",
        views.project_update,
        name="projects-project-update",
    ),
    path(
        r"project/<int:project_id>/suggestions/",
        views.presuggest_task,
        name="projects-project-tasks-suggest",
    ),
    path(
        r"project/partage/<str:project_ro_key>/",
        views.project_detail_from_sharing_link,
        name="projects-project-sharing-link",
    ),
    path(
        r"project/<int:project_id>/accept/",
        views.project_accept,
        name="projects-project-accept",
    ),
    path(
        r"project/<int:project_id>/delete/",
        views.project_delete,
        name="projects-project-delete",
    ),
    path(
        r"project/<int:project_id>/task/",
        views.create_task,
        name="projects-create-task",
    ),
    path(
        r"task/<int:task_id>/update/",
        views.update_task,
        name="projects-update-task",
    ),
    path(
        r"task/<int:task_id>/visit/",
        views.visit_task,
        name="projects-visit-task",
    ),
    path(
        r"task/<int:task_id>/toggle-done/",
        views.toggle_done_task,
        name="projects-toggle-done-task",
    ),
    path(
        r"task/<int:task_id>/refuse/",
        views.refuse_task,
        name="projects-refuse-task",
    ),
    path(
        r"task/<int:task_id>/already/",
        views.already_done_task,
        name="projects-already-done-task",
    ),
    path(
        r"task/<int:task_id>/delete/",
        views.delete_task,
        name="projects-delete-task",
    ),
    path(
        r"task/<int:task_id>/remind/",
        views.remind_task,
        name="projects-remind-task",
    ),
    path(
        r"task/<int:task_id>/followup/",
        views.followup_task,
        name="projects-followup-task",
    ),
    path(
        r"task/rsvp/<uuid:rsvp_id>/<int:status>/",
        views.rsvp_followup_task,
        name="projects-rsvp-followup-task",
    ),
    path(
        r"project/<int:project_id>/note/",
        views.create_note,
        name="projects-create-note",
    ),
    path(
        r"note/<int:note_id>/delete/",
        views.delete_note,
        name="projects-delete-note",
    ),
    path(
        r"note/<int:note_id>/",
        views.update_note,
        name="projects-update-note",
    ),
    path(
        r"project/<int:resource_id>/resource/action/",
        views.create_resource_action,
        name="projects-create-resource-action",
    ),
    path(
        r"project/<int:project_id>/access/",
        views.access_update,
        name="projects-access-update",
    ),
    path(
        r"project/<int:project_id>/access/<str:email>/delete",
        views.access_delete,
        name="projects-access-delete",
    ),
    # Recommendations
    path(
        r"projects/task-recommendation",
        views.task_recommendation_list,
        name="projects-task-recommendation-list",
    ),
    path(
        r"projects/task-recommendation/create",
        views.task_recommendation_create,
        name="projects-task-recommendation-create",
    ),
    path(
        r"projects/task-recommendation/<int:recommendation_id>/update",
        views.task_recommendation_update,
        name="projects-task-recommendation-update",
    ),
]

# eof
