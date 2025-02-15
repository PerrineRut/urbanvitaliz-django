# encoding: utf-8

"""
Models for project

author  : raphael.marvie@beta.gouv.fr,guillaume.libersat@beta.gouv.fr
created : 2021-05-26 13:33:11 CEST
"""

import uuid

from django.contrib.auth import models as auth_models
from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from django.urls import reverse
from django.utils import timezone
from markdownx.utils import markdownify
from tagging.fields import TagField
from tagging.models import TaggedItem
from tagging.registry import register as tagging_register
from urbanvitaliz.apps.addressbook import models as addressbook_models
from urbanvitaliz.apps.geomatics import models as geomatics_models
from urbanvitaliz.apps.reminders import models as reminders_models
from urbanvitaliz.apps.resources import models as resources

from .utils import generate_ro_key


class ProjectQuerySet(models.QuerySet):
    """QuerySet for active projects"""

    def email(self, mail):
        """Return projects accessible to given email"""
        return self.filter(emails__contains=mail, deleted=None)

    def in_departments(self, departments):
        """Return only project with commune in department scope (empty=full)"""
        result = self.filter(deleted=None)
        if departments:
            result = result.filter(commune__department__in=departments)
        return result


class DeletedProjectManager(models.Manager):
    """Manager for deleted projects"""

    def get_queryset(self):
        return super().get_queryset().exclude(deleted=None)


class Project(models.Model):
    """Représente un project de suivi d'une collectivité"""

    objects = ProjectQuerySet.as_manager()
    objects_deleted = DeletedProjectManager()

    email = models.CharField(max_length=128)
    emails = models.JSONField(default=list)  # list of person having access to project

    ro_key = models.CharField(
        max_length=32,
        editable=False,
        verbose_name="Clé d'accès lecture seule",
        default=generate_ro_key,
        unique=True,
    )

    last_name = models.CharField(
        max_length=128, default="", verbose_name="Nom du contact"
    )
    first_name = models.CharField(
        max_length=128, default="", verbose_name="Prénom du contact"
    )

    publish_to_cartofriches = models.BooleanField(
        verbose_name="Publier sur cartofriches", default=False
    )

    @property
    def full_name(self):
        return " ".join([self.first_name, self.last_name])

    @property
    def has_blocked_action(self):
        # return self.tasks.filter(status=Task.BLOCKED).count() > 0
        # XXX Uncomment me once status is written
        return False

    is_draft = models.BooleanField(default=True, blank=True)

    exclude_stats = models.BooleanField(default=False)

    org_name = models.CharField(
        max_length=256, blank=True, default="", verbose_name="Nom de votre structure"
    )

    created_on = models.DateTimeField(
        default=timezone.now, verbose_name="Date de création"
    )
    updated_on = models.DateTimeField(
        default=timezone.now, verbose_name="Dernière mise à jour"
    )
    tags = models.CharField(max_length=256, blank=True, default="")

    name = models.CharField(max_length=128, verbose_name="Nom du projet")
    phone = models.CharField(
        max_length=16, default="", blank=True, verbose_name="Téléphone"
    )
    description = models.TextField(verbose_name="Description", default="", blank=True)
    location = models.CharField(max_length=256, verbose_name="Localisation")
    commune = models.ForeignKey(
        geomatics_models.Commune,
        null=True,
        on_delete=models.CASCADE,
        verbose_name="Commune",
    )
    impediments = models.TextField(default="", blank=True, verbose_name="Difficultés")

    switchtender = models.ForeignKey(
        auth_models.User,
        on_delete=models.SET_NULL,
        related_name="projects_managed",
        null=True,
        blank=True,
        verbose_name="Aiguilleu·r·se",
    )

    @property
    def resources(self):
        return self.tasks.exclude(resource=None)

    deleted = models.DateTimeField(null=True, blank=True)

    def get_absolute_url(self):
        return reverse("projects-project-detail", kwargs={"project_id": self.pk})

    class Meta:
        verbose_name = "project"
        verbose_name_plural = "projects"
        permissions = (
            ("can_administrate_project", ("Aiguilleuse > Peut administrer un projet")),
        )

    def __str__(self):  # pragma: nocover
        return f"{self.name} {self.location}"

    @classmethod
    def fetch(cls, email=None):
        projects = cls.objects.filter(deleted=None)
        if email:
            projects = projects.filter(emails__contains=email)
        return projects


class NoteManager(models.Manager):
    """Manager for active tasks"""

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .order_by("-created_on", "-updated_on")
            .filter(deleted=None)
        )

    def public(self):
        return self.filter(public=True)


class Note(models.Model):
    """Représente un suivi de project"""

    objects = NoteManager()

    project = models.ForeignKey(
        "Project", on_delete=models.CASCADE, related_name="notes"
    )
    public = models.BooleanField(default=False, blank=True)
    created_on = models.DateTimeField(
        default=timezone.now, verbose_name="date de création"
    )
    updated_on = models.DateTimeField(
        default=timezone.now, verbose_name="Dernière mise à jour"
    )
    tags = models.CharField(max_length=256, blank=True, default="")

    def tags_as_list(self):
        """
        Needed since django doesn't provide a split template tag
        """
        tags = []

        words = self.tags.split(" ")
        for word in words:
            tag = word.strip(" ")
            if tag != "":
                tags.append(tag)

        return tags

    content = models.TextField(default="")

    @property
    def content_rendered(self):
        """Return content as markdown"""
        return markdownify(self.content)

    deleted = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = []
        verbose_name = "note"
        verbose_name_plural = "notes"

    def __str__(self):  # pragma: nocover
        return f"Note: #{self.id}"

    @classmethod
    def fetch(cls):
        return cls.objects.filter(deleted=None)


class TaskManager(models.Manager):
    """Manager for active tasks"""

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .order_by("-priority", "-updated_on")
            .filter(deleted=None)
        )

    #     def visited(self):
    #         return self.filter(visited=True, refused=False)

    def proposed(self):
        return self.filter(visited=False, refused=False)

    def refused(self):
        return self.filter(refused=True, done=False)

    #     def already_done(self):
    #         return self.filter(refused=True, done=True)
    #
    #     def done(self):
    #         return self.filter(visited=True, done=True, refused=False)

    def done_or_already_done(self):
        return self.filter(done=True)

    def open(self):
        return self.filter(done=False, refused=False)


class DeletedTaskManager(models.Manager):
    """Manager for deleted tasks"""

    def get_queryset(self):
        return super().get_queryset().exclude(deleted=None)


class Task(models.Model):
    """Représente une action pour faire avancer un project"""

    objects = TaskManager()
    deleted_objects = DeletedTaskManager()

    INPROGRESS = 1
    BLOCKED = 2
    DONE = 3
    REFUSED = 4

    STATUS_CHOICES = (
        (INPROGRESS, "en cours"),
        (BLOCKED, "blocage"),
        (DONE, "terminé"),
        (REFUSED, "refusé"),
    )

    project = models.ForeignKey(
        "Project", on_delete=models.CASCADE, related_name="tasks"
    )
    public = models.BooleanField(default=False, blank=True)
    priority = models.PositiveIntegerField(
        default=0,
        blank=True,
        verbose_name="Priorité",
        help_text=(
            "Plus le chiffre est élevé, plus la recommandation s'affichera en haut."
        ),
    )

    created_by = models.ForeignKey(
        auth_models.User, on_delete=models.CASCADE, related_name="tasks_created"
    )

    created_on = models.DateTimeField(
        default=timezone.now, verbose_name="date de création"
    )
    updated_on = models.DateTimeField(
        default=timezone.now, verbose_name="Dernière mise à jour"
    )
    tags = models.CharField(max_length=256, blank=True, default="")

    #     def tags_as_list(self):
    #         """
    #         Needed since django doesn't provide a split template tag
    #         """
    #         tags = []
    #
    #         words = self.tags.split(" ")
    #         for word in words:
    #             tag = word.strip(" ")
    #             if tag != "":
    #                 tags.append(tag)
    #
    #         return tags

    intent = models.CharField(
        max_length=256, blank=True, default="", verbose_name="Intention"
    )
    content = models.TextField(default="", verbose_name="Contenu")

    @property
    def content_rendered(self):
        """Return content as markdown"""
        return markdownify(self.content)

    deadline = models.DateField(null=True, blank=True)

    resource = models.ForeignKey(
        resources.Resource, on_delete=models.CASCADE, null=True, blank=True
    )

    contact = models.ForeignKey(
        addressbook_models.Contact, on_delete=models.CASCADE, null=True, blank=True
    )

    #     @property
    #     def is_deadline_past_due(self):
    #         return date.today() > self.deadline if self.deadline else False

    visited = models.BooleanField(default=False, blank=True)
    refused = models.BooleanField(default=False, blank=True)
    done = models.BooleanField(default=False, blank=True)

    deleted = models.DateTimeField(null=True, blank=True)

    reminders = GenericRelation(reminders_models.Mail, related_query_name="tasks")

    class Meta:
        ordering = []
        verbose_name = "action"
        verbose_name_plural = "actions"

    def __str__(self):  # pragma: nocover
        return "Task:{0}".format(self.intent or self.id)

    def get_absolute_url(self):
        return reverse("projects-project-detail", args=[self.project.id]) + "#actions"


class TaskFollowup(models.Model):
    """An followup on the task -- achievements and comments"""

    task = models.ForeignKey("Task", on_delete=models.CASCADE, related_name="followups")
    who = models.ForeignKey(
        auth_models.User, on_delete=models.CASCADE, related_name="task_followups"
    )
    status = models.IntegerField(choices=Task.STATUS_CHOICES)

    @property
    def status_txt(self):
        return {
            Task.INPROGRESS: "en cours",
            Task.BLOCKED: "bloquée",
            Task.DONE: "terminée",
            Task.REFUSED: "rejetée",
        }.get(self.status, "?")

    timestamp = models.DateTimeField(default=timezone.now)
    comment = models.TextField(default="", blank=True)

    class Meta:
        verbose_name = "suivi action"
        verbose_name_plural = "suivis actions"

    def __str__(self):  # pragma: nocover
        return f"TaskFollowup{self.id}"


class TaskFollowupRsvp(models.Model):
    """Task followup request sent to project owner."""

    uuid = models.UUIDField(default=uuid.uuid4, primary_key=True)
    task = models.ForeignKey(
        "Task", on_delete=models.CASCADE, related_name="rsvp_followups"
    )
    created_on = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = "rsvp suivi action"
        verbose_name_plural = "rsvp suivis actions"

    def __str__(self):  # pragma: nocover
        return f"TaskFollowupRsvp{self.uuid}"


class TaskRecommendationManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().order_by("resource__title")


class TaskRecommendation(models.Model):
    """Recommendation mechanisms for Tasks"""

    objects = TaskRecommendationManager()

    condition = TagField(verbose_name="Condition", blank=True, null=True)
    resource = models.ForeignKey(resources.Resource, on_delete=models.CASCADE)
    text = models.TextField()
    departments = models.ManyToManyField(
        geomatics_models.Department,
        blank=True,
        verbose_name="Départements concernés",
    )

    def trigged_by(self):
        from urbanvitaliz.apps.survey import models as survey_models

        triggers = {}
        for tag in self.condition_tags:
            triggers[tag] = TaggedItem.objects.get_by_model(survey_models.Choice, tag)

        return triggers

    def __str__(self):
        return f"{self.resource.title} - {self.text}"


tagging_register(TaskRecommendation, tag_descriptor_attr="condition_tags")


class Document(models.Model):
    """Représente un document associé à un project"""

    project = models.ForeignKey("Project", on_delete=models.CASCADE)
    public = models.BooleanField(default=False, blank=True)
    created_on = models.DateTimeField(
        default=timezone.now, verbose_name="date de création"
    )
    tags = models.CharField(max_length=256, blank=True, default="")

    description = models.CharField(max_length=256, default="", blank=True)
    the_file = models.FileField()

    deleted = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = []
        verbose_name = "document"
        verbose_name_plural = "documents"

    def __str__(self):  # pragma: nocover
        return f"Document {self.id}"


# eof
