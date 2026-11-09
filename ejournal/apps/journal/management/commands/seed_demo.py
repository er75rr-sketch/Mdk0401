"""python manage.py seed_demo — заполняет базу демонстрационными данными."""
import random
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.journal.models import Attendance, Grade, Lesson
from apps.students.models import Student, StudyGroup
from apps.subjects.models import Subject, TeacherAssignment

User = get_user_model()

STUDENTS = {
    "ИС-21": [
        ("Иванов", "Иван", "Сергеевич"), ("Смирнова", "Ольга", "Андреевна"),
        ("Кузнецов", "Дмитрий", "Игоревич"), ("Попова", "Анна", "Викторовна"),
        ("Васильев", "Артём", "Олегович"), ("Соколова", "Мария", "Денисовна"),
        ("Морозов", "Никита", "Павлович"), ("Новикова", "Екатерина", "Романовна"),
    ],
    "ИС-22": [
        ("Фёдоров", "Максим", "Алексеевич"), ("Волкова", "Дарья", "Сергеевна"),
        ("Алексеев", "Кирилл", "Иванович"), ("Лебедева", "Полина", "Олеговна"),
        ("Семёнов", "Егор", "Николаевич"), ("Егорова", "Алина", "Дмитриевна"),
        ("Павлов", "Илья", "Викторович"), ("Козлова", "Виктория", "Андреевна"),
    ],
}

TOPICS = {
    "Математика": ["Пределы", "Производная", "Интеграл", "Ряды", "Матрицы", "Определители"],
    "Базы данных": ["Реляционная модель", "SELECT", "JOIN", "Нормализация", "Индексы", "Транзакции"],
    "Веб-программирование": ["HTML", "CSS", "JavaScript", "Django: модели", "Django: представления", "REST API"],
}


class Command(BaseCommand):
    help = "Создаёт демо-пользователей, группы, студентов, дисциплины, занятия, оценки и посещаемость."

    def add_arguments(self, parser):
        parser.add_argument("--force", action="store_true", help="Добавить данные, даже если группы уже есть")

    def _user(self, username, password, role, last, first, middle="", superuser=False):
        user, created = User.objects.get_or_create(
            username=username,
            defaults={"role": role, "last_name": last, "first_name": first, "middle_name": middle,
                      "is_staff": superuser, "is_superuser": superuser},
        )
        if created:
            user.set_password(password)
            user.save()
        return user

    @transaction.atomic
    def handle(self, *args, **options):
        if StudyGroup.objects.exists() and not options["force"]:
            self.stdout.write(self.style.WARNING("Данные уже есть. Для повторного заполнения: seed_demo --force"))
            return

        rnd = random.Random(42)
        self._user("admin", "Admin12345", "admin", "Администратор", "Системы", superuser=True)
        t_math = self._user("petrova", "Teacher12345", "curator", "Петрова", "Анна", "Михайловна")
        t_db = self._user("orlov", "Teacher12345", "teacher", "Орлов", "Сергей", "Викторович")
        t_web = self._user("belova", "Teacher12345", "curator", "Белова", "Ирина", "Петровна")

        g21, _ = StudyGroup.objects.get_or_create(
            name="ИС-21", defaults={"course": 2, "specialty": "09.02.07 Информационные системы и программирование",
                                    "curator": t_math})
        g22, _ = StudyGroup.objects.get_or_create(
            name="ИС-22", defaults={"course": 2, "specialty": "09.02.07 Информационные системы и программирование",
                                    "curator": t_web})
        groups = {"ИС-21": g21, "ИС-22": g22}

        for gname, people in STUDENTS.items():
            for i, (last, first, middle) in enumerate(people, start=1):
                user = None
                if gname == "ИС-21" and i == 1:
                    user = self._user("ivanov", "Student12345", "student", last, first, middle)
                    user.is_staff = False
                    user.save()
                Student.objects.get_or_create(
                    record_book=f"{gname[-2:]}-{i:03d}",
                    defaults={"last_name": last, "first_name": first, "middle_name": middle,
                              "group": groups[gname], "user": user},
                )

        subjects = {
            "Математика": Subject.objects.get_or_create(code="ЕН.01", defaults={"name": "Математика", "hours": 108})[0],
            "Базы данных": Subject.objects.get_or_create(code="ОП.08", defaults={"name": "Базы данных", "hours": 96})[0],
            "Веб-программирование": Subject.objects.get_or_create(
                code="МДК.09.01", defaults={"name": "Веб-программирование", "hours": 120})[0],
        }
        teachers = {"Математика": t_math, "Базы данных": t_db, "Веб-программирование": t_web}

        today = timezone.localdate()
        for group in groups.values():
            for subj_name, subject in subjects.items():
                assignment, _ = TeacherAssignment.objects.get_or_create(
                    subject=subject, group=group, defaults={"teacher": teachers[subj_name]}
                )
                for n, topic in enumerate(TOPICS[subj_name]):
                    lesson = Lesson.objects.create(
                        assignment=assignment, topic=topic,
                        date=today - timedelta(days=(len(TOPICS[subj_name]) - n) * 3),
                        lesson_type=Lesson.Type.CONTROL if n == len(TOPICS[subj_name]) - 1 else Lesson.Type.PRACTICE,
                    )
                    for student in group.students.all():
                        roll = rnd.random()
                        if roll < 0.08:
                            Attendance.objects.create(lesson=lesson, student=student, status=Attendance.Status.ABSENT)
                            continue
                        status = Attendance.Status.LATE if roll < 0.13 else Attendance.Status.PRESENT
                        Attendance.objects.create(lesson=lesson, student=student, status=status)
                        if rnd.random() < 0.6:
                            value = rnd.choices([5, 4, 3, 2], weights=[35, 40, 20, 5])[0]
                            Grade.objects.create(lesson=lesson, student=student, value=value)

        self.stdout.write(self.style.SUCCESS("Демо-данные созданы."))
        self.stdout.write("Вход: admin / Admin12345 (администратор)")
        self.stdout.write("      petrova / Teacher12345 (преподаватель-куратор ИС-21)")
        self.stdout.write("      orlov / Teacher12345 (преподаватель)")
        self.stdout.write("      ivanov / Student12345 (студент ИС-21)")
