from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class StudyGroup(models.Model):
    """Учебная группа (например, ИС-21)."""
    name = models.CharField("Название", max_length=20, unique=True)
    course = models.PositiveSmallIntegerField(
        "Курс", validators=[MinValueValidator(1), MaxValueValidator(4)], default=1
    )
    specialty = models.CharField("Специальность", max_length=200, blank=True)
    curator = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="Куратор", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="curated_groups",
        limit_choices_to={"role__in": ["curator", "teacher"]},
    )

    class Meta:
        verbose_name = "Группа"
        verbose_name_plural = "Группы"
        ordering = ["course", "name"]

    def __str__(self):
        return self.name


class Student(models.Model):
    """Студент группы. Может быть привязан к учётной записи для входа."""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, verbose_name="Учётная запись", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="student_profile",
        limit_choices_to={"role": "student"},
    )
    last_name = models.CharField("Фамилия", max_length=100)
    first_name = models.CharField("Имя", max_length=100)
    middle_name = models.CharField("Отчество", max_length=100, blank=True)
    group = models.ForeignKey(
        StudyGroup, verbose_name="Группа", on_delete=models.PROTECT, related_name="students"
    )
    record_book = models.CharField("№ зачётной книжки", max_length=20, unique=True)
    birth_date = models.DateField("Дата рождения", null=True, blank=True)
    email = models.EmailField("E-mail", blank=True)
    is_active = models.BooleanField("Обучается", default=True)

    class Meta:
        verbose_name = "Студент"
        verbose_name_plural = "Студенты"
        ordering = ["group__name", "last_name", "first_name"]

    @property
    def full_name(self):
        return " ".join(p for p in [self.last_name, self.first_name, self.middle_name] if p)

    def __str__(self):
        return f"{self.full_name} ({self.group})"
