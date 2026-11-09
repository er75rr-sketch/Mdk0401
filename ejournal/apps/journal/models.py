from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from apps.students.models import Student
from apps.subjects.models import TeacherAssignment


def student_lesson_error(student, lesson):
    """Текст ошибки, если студент не из группы, где проходит занятие; иначе None."""
    if student.group_id != lesson.assignment.group_id:
        return f"Студент {student.full_name} не учится в группе {lesson.assignment.group}."
    return None


class Lesson(models.Model):
    """Проведённое занятие по нагрузке преподавателя."""

    class Type(models.TextChoices):
        LECTURE = "lecture", "Лекция"
        PRACTICE = "practice", "Практическое занятие"
        LAB = "lab", "Лабораторная работа"
        CONTROL = "control", "Контрольная работа"

    assignment = models.ForeignKey(
        TeacherAssignment, verbose_name="Дисциплина / группа", on_delete=models.PROTECT,
        related_name="lessons",
    )
    date = models.DateField("Дата", default=timezone.localdate)
    topic = models.CharField("Тема", max_length=255)
    lesson_type = models.CharField("Вид занятия", max_length=20, choices=Type.choices, default=Type.PRACTICE)

    class Meta:
        verbose_name = "Занятие"
        verbose_name_plural = "Занятия"
        ordering = ["-date", "-id"]

    @property
    def group(self):
        return self.assignment.group

    @property
    def subject(self):
        return self.assignment.subject

    def __str__(self):
        return f"{self.date:%d.%m.%Y} {self.assignment.subject.name} ({self.assignment.group}): {self.topic}"


class Grade(models.Model):
    """Оценка студента за занятие."""
    VALUES = [(5, "5 — отлично"), (4, "4 — хорошо"), (3, "3 — удовлетворительно"), (2, "2 — неудовлетворительно")]

    lesson = models.ForeignKey(Lesson, verbose_name="Занятие", on_delete=models.CASCADE, related_name="grades")
    student = models.ForeignKey(Student, verbose_name="Студент", on_delete=models.CASCADE, related_name="grades")
    value = models.PositiveSmallIntegerField(
        "Оценка", choices=VALUES, validators=[MinValueValidator(2), MaxValueValidator(5)]
    )
    comment = models.CharField("Комментарий", max_length=255, blank=True)
    created_at = models.DateTimeField("Выставлена", auto_now_add=True)

    class Meta:
        verbose_name = "Оценка"
        verbose_name_plural = "Оценки"
        ordering = ["-lesson__date", "student__last_name"]
        unique_together = [("lesson", "student")]

    def clean(self):
        if self.lesson_id and self.student_id:
            error = student_lesson_error(self.student, self.lesson)
            if error:
                raise ValidationError({"student": error})
            if Attendance.objects.filter(
                lesson_id=self.lesson_id, student_id=self.student_id, status=Attendance.Status.ABSENT
            ).exists():
                raise ValidationError({"value": "Нельзя поставить оценку студенту, отмеченному как отсутствующий."})

    def __str__(self):
        return f"{self.student.full_name}: {self.value}"


class Attendance(models.Model):
    """Отметка посещаемости студента на занятии."""

    class Status(models.TextChoices):
        PRESENT = "present", "Присутствовал"
        ABSENT = "absent", "Отсутствовал (н)"
        LATE = "late", "Опоздал"
        EXCUSED = "excused", "Уважительная причина"

    lesson = models.ForeignKey(Lesson, verbose_name="Занятие", on_delete=models.CASCADE, related_name="attendance")
    student = models.ForeignKey(Student, verbose_name="Студент", on_delete=models.CASCADE, related_name="attendance")
    status = models.CharField("Отметка", max_length=10, choices=Status.choices, default=Status.PRESENT)

    class Meta:
        verbose_name = "Посещаемость"
        verbose_name_plural = "Посещаемость"
        ordering = ["-lesson__date", "student__last_name"]
        unique_together = [("lesson", "student")]

    def clean(self):
        if self.lesson_id and self.student_id:
            error = student_lesson_error(self.student, self.lesson)
            if error:
                raise ValidationError({"student": error})
            if self.status == self.Status.ABSENT and Grade.objects.filter(
                lesson_id=self.lesson_id, student_id=self.student_id
            ).exists():
                raise ValidationError({"status": "У студента есть оценка за это занятие — он не может быть отсутствующим."})

    def __str__(self):
        return f"{self.student.full_name}: {self.get_status_display()}"


@receiver(post_save, sender=Grade)
def mark_present_on_grade(sender, instance, created, **kwargs):
    """Каскад: выставили оценку — студент автоматически отмечен как присутствовавший."""
    if created:
        Attendance.objects.get_or_create(
            lesson=instance.lesson, student=instance.student,
            defaults={"status": Attendance.Status.PRESENT},
        )
