"""Интеграционные тесты: accounts + students + subjects + journal работают вместе."""
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from apps.students.models import Student, StudyGroup
from apps.subjects.models import Subject, TeacherAssignment

from .models import Attendance, Grade, Lesson

User = get_user_model()


class JournalTestData(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(username="adm", password="Admin12345", role="admin")
        self.t1 = User.objects.create_user(username="t1", password="Teacher12345", role="teacher")
        self.t2 = User.objects.create_user(username="t2", password="Teacher12345", role="teacher")
        self.st_user = User.objects.create_user(username="ivanov", password="Student12345", role="student")

        self.g1 = StudyGroup.objects.create(name="ИС-21", course=2)
        self.g2 = StudyGroup.objects.create(name="ИС-22", course=2)
        self.ivanov = Student.objects.create(
            last_name="Иванов", first_name="Иван", group=self.g1, record_book="21-001", user=self.st_user
        )
        self.petrov = Student.objects.create(last_name="Петров", first_name="Пётр", group=self.g1, record_book="21-002")
        self.sidorov = Student.objects.create(last_name="Сидоров", first_name="Сидор", group=self.g2, record_book="22-001")

        self.math = Subject.objects.create(code="ЕН.01", name="Математика")
        self.a1 = TeacherAssignment.objects.create(teacher=self.t1, subject=self.math, group=self.g1)
        self.a2 = TeacherAssignment.objects.create(teacher=self.t2, subject=self.math, group=self.g2)
        self.lesson = Lesson.objects.create(assignment=self.a1, topic="Производная")


class LessonTests(JournalTestData):
    def test_teacher_creates_lesson_for_own_assignment(self):
        self.client.force_authenticate(self.t1)
        resp = self.client.post("/api/lessons/", {"assignment": self.a1.id, "topic": "Интеграл", "date": "2026-10-01"})
        self.assertEqual(resp.status_code, 201, resp.data)
        self.assertEqual(resp.data["group_name"], "ИС-21")

    def test_teacher_cannot_create_lesson_for_foreign_assignment(self):
        self.client.force_authenticate(self.t1)
        resp = self.client.post("/api/lessons/", {"assignment": self.a2.id, "topic": "Чужое", "date": "2026-10-01"})
        self.assertEqual(resp.status_code, 403)

    def test_student_cannot_create_lesson(self):
        self.client.force_authenticate(self.st_user)
        resp = self.client.post("/api/lessons/", {"assignment": self.a1.id, "topic": "x"})
        self.assertEqual(resp.status_code, 403)

    def test_sheet(self):
        Grade.objects.create(lesson=self.lesson, student=self.ivanov, value=5)
        self.client.force_authenticate(self.t1)
        resp = self.client.get(f"/api/lessons/{self.lesson.id}/sheet/")
        self.assertEqual(resp.status_code, 200)
        rows = {r["student"]: r for r in resp.data["students"]}
        self.assertEqual(rows["Иванов Иван"]["grade"], 5)
        self.assertEqual(rows["Иванов Иван"]["attendance"], "Присутствовал")
        self.assertIsNone(rows["Петров Пётр"]["grade"])


class GradeTests(JournalTestData):
    def test_grade_creates_attendance_cascade(self):
        self.client.force_authenticate(self.t1)
        resp = self.client.post("/api/grades/", {"lesson": self.lesson.id, "student": self.ivanov.id, "value": 4})
        self.assertEqual(resp.status_code, 201, resp.data)
        att = Attendance.objects.get(lesson=self.lesson, student=self.ivanov)
        self.assertEqual(att.status, "present")

    def test_grade_for_student_of_other_group_rejected(self):
        self.client.force_authenticate(self.t1)
        resp = self.client.post("/api/grades/", {"lesson": self.lesson.id, "student": self.sidorov.id, "value": 5})
        self.assertEqual(resp.status_code, 400)
        self.assertIn("student", resp.data)

    def test_grade_for_absent_student_rejected(self):
        Attendance.objects.create(lesson=self.lesson, student=self.petrov, status="absent")
        self.client.force_authenticate(self.t1)
        resp = self.client.post("/api/grades/", {"lesson": self.lesson.id, "student": self.petrov.id, "value": 5})
        self.assertEqual(resp.status_code, 400)

    def test_invalid_value_rejected(self):
        self.client.force_authenticate(self.t1)
        resp = self.client.post("/api/grades/", {"lesson": self.lesson.id, "student": self.ivanov.id, "value": 6})
        self.assertEqual(resp.status_code, 400)

    def test_duplicate_grade_rejected(self):
        Grade.objects.create(lesson=self.lesson, student=self.ivanov, value=5)
        self.client.force_authenticate(self.t1)
        resp = self.client.post("/api/grades/", {"lesson": self.lesson.id, "student": self.ivanov.id, "value": 3})
        self.assertEqual(resp.status_code, 400)

    def test_other_teacher_cannot_grade(self):
        self.client.force_authenticate(self.t2)
        resp = self.client.post("/api/grades/", {"lesson": self.lesson.id, "student": self.ivanov.id, "value": 5})
        self.assertEqual(resp.status_code, 403)

    def test_other_teacher_cannot_edit_grade(self):
        grade = Grade.objects.create(lesson=self.lesson, student=self.ivanov, value=5)
        self.client.force_authenticate(self.t2)
        resp = self.client.patch(f"/api/grades/{grade.id}/", {"value": 2})
        self.assertIn(resp.status_code, (403, 404))

    def test_student_sees_only_own_grades(self):
        Grade.objects.create(lesson=self.lesson, student=self.ivanov, value=5)
        Grade.objects.create(lesson=self.lesson, student=self.petrov, value=3)
        self.client.force_authenticate(self.st_user)
        resp = self.client.get("/api/grades/")
        self.assertEqual(resp.data["count"], 1)
        self.assertEqual(resp.data["results"][0]["student_name"], "Иванов Иван")


class AttendanceTests(JournalTestData):
    def test_mark_absent(self):
        self.client.force_authenticate(self.t1)
        resp = self.client.post("/api/attendance/", {"lesson": self.lesson.id, "student": self.petrov.id, "status": "absent"})
        self.assertEqual(resp.status_code, 201, resp.data)

    def test_cannot_mark_absent_when_grade_exists(self):
        Grade.objects.create(lesson=self.lesson, student=self.ivanov, value=5)
        att = Attendance.objects.get(lesson=self.lesson, student=self.ivanov)
        self.client.force_authenticate(self.t1)
        resp = self.client.patch(f"/api/attendance/{att.id}/", {"status": "absent"})
        self.assertEqual(resp.status_code, 400)
