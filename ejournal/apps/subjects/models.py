from django.conf import settings
from django.db import models

from apps.students.models import StudyGroup


class Subject(models.Model):
    """Учебная дисциплина."""
    code = models.CharField("Код", max_length=20, unique=True)
    name = models.CharField("Название", max_length=200)
    hours = models.PositiveSmallIntegerField("Часов", default=72)

    class Meta:
        verbose_name = "Дисциплина"
        verbose_name_plural = "Дисциплины"
        ordering = ["name"]

    def __str__(self):
        return f"{self.code} {self.name}"


class TeacherAssignment(models.Model):
    """Нагрузка: какой преподаватель ведёт какую дисциплину в какой группе."""
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="Преподаватель", on_delete=models.PROTECT,
        related_name="assignments", limit_choices_to={"role__in": ["teacher", "curator"]},
    )
    subject = models.ForeignKey(
        Subject, verbose_name="Дисциплина", on_delete=models.PROTECT, related_name="assignments"
    )
    group = models.ForeignKey(
        StudyGroup, verbose_name="Группа", on_delete=models.PROTECT, related_name="assignments"
    )

    class Meta:
        verbose_name = "Нагрузка преподавателя"
        verbose_name_plural = "Нагрузка преподавателей"
        ordering = ["group__name", "subject__name"]
        unique_together = [("subject", "group")]

    def __str__(self):
        return f"{self.subject.name} — {self.group} ({self.teacher.full_name})"
