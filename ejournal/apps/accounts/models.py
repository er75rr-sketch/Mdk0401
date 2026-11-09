from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Сотрудник или студент колледжа с ролью в системе."""

    class Role(models.TextChoices):
        ADMIN = "admin", "Администратор"
        CURATOR = "curator", "Куратор"
        TEACHER = "teacher", "Преподаватель"
        STUDENT = "student", "Студент"

    role = models.CharField("Роль", max_length=20, choices=Role.choices, default=Role.TEACHER)
    middle_name = models.CharField("Отчество", max_length=150, blank=True)
    phone = models.CharField("Телефон", max_length=20, blank=True)

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
        ordering = ["last_name", "first_name"]

    def save(self, *args, **kwargs):
        # суперпользователь, созданный через createsuperuser, получает роль администратора
        if self.is_superuser and self.role == self.Role.TEACHER and not self.pk:
            self.role = self.Role.ADMIN
        super().save(*args, **kwargs)

    @property
    def is_admin_role(self):
        return self.is_superuser or self.role == self.Role.ADMIN

    @property
    def is_teacher_role(self):
        return self.role in (self.Role.TEACHER, self.Role.CURATOR)

    @property
    def full_name(self):
        parts = [self.last_name, self.first_name, self.middle_name]
        name = " ".join(p for p in parts if p)
        return name or self.username

    def __str__(self):
        return f"{self.full_name} ({self.get_role_display()})"
