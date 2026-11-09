from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from apps.journal.models import Attendance, Grade, Lesson
from apps.students.models import Student, StudyGroup
from apps.subjects.models import Subject, TeacherAssignment

User = get_user_model()


class ReportsTests(APITestCase):
    def setUp(self):
        self.teacher = User.objects.create_user(username="t1", password="Teacher12345", role="teacher")
        self.st_user = User.objects.create_user(username="s1", password="Student12345", role="student")
        self.group = StudyGroup.objects.create(name="ИС-21", course=2)
        self.s1 = Student.objects.create(last_name="Иванов", first_name="Иван", group=self.group,
                                         record_book="1", user=self.st_user)
        self.s2 = Student.objects.create(last_name="Петров", first_name="Пётр", group=self.group, record_book="2")
        subject = Subject.objects.create(code="ЕН.01", name="Математика")
        a = TeacherAssignment.objects.create(teacher=self.teacher, subject=subject, group=self.group)
        l1 = Lesson.objects.create(assignment=a, topic="Тема 1")
        l2 = Lesson.objects.create(assignment=a, topic="Тема 2")
        Grade.objects.create(lesson=l1, student=self.s1, value=5)
        Grade.objects.create(lesson=l2, student=self.s1, value=4)
        Grade.objects.create(lesson=l1, student=self.s2, value=2)
        Attendance.objects.create(lesson=l2, student=self.s2, status="absent")

    def test_kpi(self):
        self.client.force_authenticate(self.teacher)
        resp = self.client.get("/api/reports/kpi/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["grades"], 3)
        self.assertEqual(resp.data["average_grade"], 3.67)
        self.assertEqual(resp.data["underperforming_students"], 1)
        self.assertEqual(resp.data["attendance"]["absent"], 1)
        self.assertEqual(resp.data["attendance"]["total"], 4)  # 3 авто-отметки + 1 «н»

    def test_kpi_updates_after_new_grade(self):
        self.client.force_authenticate(self.teacher)
        before = self.client.get("/api/reports/kpi/").data
        lesson = Lesson.objects.create(assignment=TeacherAssignment.objects.get(), topic="Тема 3")
        resp = self.client.post("/api/grades/", {"lesson": lesson.id, "student": self.s2.id, "value": 5})
        self.assertEqual(resp.status_code, 201, resp.data)
        after = self.client.get("/api/reports/kpi/").data
        self.assertEqual(after["grades"], before["grades"] + 1)
        self.assertEqual(after["lessons"], before["lessons"] + 1)
        self.assertEqual(after["average_grade"], 4.0)

    def test_group_report(self):
        self.client.force_authenticate(self.teacher)
        resp = self.client.get(f"/api/reports/groups/{self.group.id}/")
        self.assertEqual(resp.status_code, 200)
        first, second = resp.data["students"]
        self.assertEqual(first["student"], "Иванов Иван")
        self.assertEqual(first["average_grade"], 4.5)
        self.assertEqual(second["absences"], 1)

    def test_student_cannot_see_kpi(self):
        self.client.force_authenticate(self.st_user)
        self.assertEqual(self.client.get("/api/reports/kpi/").status_code, 403)

    def test_student_report_own_only(self):
        self.client.force_authenticate(self.st_user)
        self.assertEqual(self.client.get(f"/api/reports/students/{self.s1.id}/").status_code, 200)
        self.assertEqual(self.client.get(f"/api/reports/students/{self.s2.id}/").status_code, 403)

    def test_api_root_lists_endpoints(self):
        resp = self.client.get("/api/")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("kpi", resp.data["reports"])
