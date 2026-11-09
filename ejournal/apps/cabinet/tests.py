from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.journal.models import Attendance, Grade, Lesson
from apps.students.models import Student, StudyGroup
from apps.subjects.models import Subject, TeacherAssignment

User = get_user_model()


class CabinetTests(TestCase):
    def setUp(self):
        self.teacher = User.objects.create_user(username="t1", password="Teacher12345", role="teacher",
                                                last_name="Петрова", first_name="Анна")
        self.st_user = User.objects.create_user(username="s1", password="Student12345", role="student")
        group = StudyGroup.objects.create(name="ИС-21", course=2)
        self.student = Student.objects.create(last_name="Иванов", first_name="Иван", group=group,
                                              record_book="21-001", user=self.st_user)
        other = Student.objects.create(last_name="Петров", first_name="Пётр", group=group, record_book="21-002")
        a = TeacherAssignment.objects.create(teacher=self.teacher, subject=Subject.objects.create(
            code="ЕН.01", name="Математика"), group=group)
        l1 = Lesson.objects.create(assignment=a, topic="Производная")
        l2 = Lesson.objects.create(assignment=a, topic="Интеграл")
        Grade.objects.create(lesson=l1, student=self.student, value=5)
        Attendance.objects.create(lesson=l2, student=self.student, status="absent")
        Grade.objects.create(lesson=l1, student=other, value=2)

    def test_anonymous_redirected_to_login(self):
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(resp["Location"].startswith("/login/"))

    def test_login_page(self):
        self.assertEqual(self.client.get("/login/").status_code, 200)

    def test_student_sees_own_diary(self):
        self.client.login(username="s1", password="Student12345")
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)
        html = resp.content.decode()
        self.assertIn("Иванов Иван", html)
        self.assertIn("Математика", html)
        self.assertIn("Интеграл", html)
        self.assertNotIn("Петров Пётр", html)
        self.assertEqual(resp.context["average"], 5.0)
        self.assertEqual(resp.context["attendance"]["absent"], 1)

    def test_teacher_gets_own_page(self):
        self.client.login(username="t1", password="Teacher12345")
        self.assertContains(self.client.get("/"), "Моя нагрузка")

    def test_logout(self):
        self.client.login(username="s1", password="Student12345")
        resp = self.client.post("/logout/")
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(self.client.get("/").status_code, 302)


class TeacherCabinetTests(TestCase):
    def setUp(self):
        self.t1 = User.objects.create_user(username="t1", password="Teacher12345", role="curator",
                                           last_name="Петрова", first_name="Анна")
        self.t2 = User.objects.create_user(username="t2", password="Teacher12345", role="teacher")
        self.st_user = User.objects.create_user(username="s1", password="Student12345", role="student")
        self.group = StudyGroup.objects.create(name="ИС-21", course=2, curator=self.t1)
        self.s1 = Student.objects.create(last_name="Иванов", first_name="Иван", group=self.group,
                                         record_book="1", user=self.st_user)
        self.s2 = Student.objects.create(last_name="Смирнова", first_name="Ольга", group=self.group, record_book="2")
        self.a1 = TeacherAssignment.objects.create(
            teacher=self.t1, subject=Subject.objects.create(code="ЕН.01", name="Математика"), group=self.group)
        self.a2 = TeacherAssignment.objects.create(
            teacher=self.t2, subject=Subject.objects.create(code="ОП.08", name="Базы данных"), group=self.group)
        self.lesson = Lesson.objects.create(assignment=self.a1, topic="Производная")

    def test_teacher_dashboard(self):
        self.client.login(username="t1", password="Teacher12345")
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Моя нагрузка")
        self.assertContains(resp, "Математика")
        self.assertNotContains(resp, "Базы данных")

    def test_create_lesson(self):
        self.client.login(username="t1", password="Teacher12345")
        resp = self.client.post("/lessons/new/", {
            "assignment": self.a1.id, "date": "2026-10-20", "topic": "Интеграл", "lesson_type": "practice"})
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(Lesson.objects.filter(topic="Интеграл").exists())

    def test_cannot_create_lesson_for_foreign_assignment(self):
        self.client.login(username="t1", password="Teacher12345")
        resp = self.client.post("/lessons/new/", {
            "assignment": self.a2.id, "date": "2026-10-20", "topic": "Чужое", "lesson_type": "practice"})
        self.assertEqual(resp.status_code, 200)  # форма с ошибкой
        self.assertFalse(Lesson.objects.filter(topic="Чужое").exists())

    def test_save_sheet(self):
        self.client.login(username="t1", password="Teacher12345")
        url = f"/lessons/{self.lesson.id}/"
        self.assertEqual(self.client.get(url).status_code, 200)
        resp = self.client.post(url, {f"grade_{self.s1.id}": "5", f"att_{self.s2.id}": "absent"})
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(Grade.objects.get(lesson=self.lesson, student=self.s1).value, 5)
        self.assertEqual(Attendance.objects.get(lesson=self.lesson, student=self.s1).status, "present")
        self.assertEqual(Attendance.objects.get(lesson=self.lesson, student=self.s2).status, "absent")

    def test_absent_with_grade_rejected(self):
        self.client.login(username="t1", password="Teacher12345")
        self.client.post(f"/lessons/{self.lesson.id}/", {f"grade_{self.s2.id}": "4", f"att_{self.s2.id}": "absent"})
        self.assertFalse(Grade.objects.filter(student=self.s2).exists())

    def test_other_teacher_cannot_edit_sheet(self):
        self.client.login(username="t2", password="Teacher12345")
        resp = self.client.post(f"/lessons/{self.lesson.id}/", {f"grade_{self.s1.id}": "2"})
        self.assertEqual(resp.status_code, 403)
        self.assertFalse(Grade.objects.exists())

    def test_student_cannot_open_sheet(self):
        self.client.login(username="s1", password="Student12345")
        self.assertEqual(self.client.get(f"/lessons/{self.lesson.id}/").status_code, 403)

    def test_curator_group_report(self):
        Grade.objects.create(lesson=self.lesson, student=self.s1, value=4)
        self.client.login(username="t1", password="Teacher12345")
        resp = self.client.get(f"/groups/{self.group.id}/report/")
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Иванов Иван")
