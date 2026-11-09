from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from apps.students.models import StudyGroup

from .models import Subject, TeacherAssignment

User = get_user_model()


class SubjectsApiTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(username="adm", password="Admin12345", role="admin")
        self.t1 = User.objects.create_user(username="t1", password="Teacher12345", role="teacher")
        self.t2 = User.objects.create_user(username="t2", password="Teacher12345", role="teacher")
        self.group = StudyGroup.objects.create(name="ИС-21", course=2)
        self.math = Subject.objects.create(code="ЕН.01", name="Математика")
        self.db = Subject.objects.create(code="ОП.08", name="Базы данных")
        TeacherAssignment.objects.create(teacher=self.t1, subject=self.math, group=self.group)
        TeacherAssignment.objects.create(teacher=self.t2, subject=self.db, group=self.group)

    def test_teacher_sees_only_own_assignments(self):
        self.client.force_authenticate(self.t1)
        resp = self.client.get("/api/assignments/")
        self.assertEqual(resp.data["count"], 1)
        self.assertEqual(resp.data["results"][0]["subject_name"], "Математика")

    def test_cannot_assign_student_as_teacher(self):
        student_user = User.objects.create_user(username="s1", password="Student12345", role="student")
        other = Subject.objects.create(code="ОП.01", name="Информатика")
        self.client.force_authenticate(self.admin)
        resp = self.client.post("/api/assignments/", {
            "teacher": student_user.id, "subject": other.id, "group": self.group.id,
        })
        self.assertEqual(resp.status_code, 400)

    def test_duplicate_subject_in_group_rejected(self):
        self.client.force_authenticate(self.admin)
        resp = self.client.post("/api/assignments/", {
            "teacher": self.t2.id, "subject": self.math.id, "group": self.group.id,
        })
        self.assertEqual(resp.status_code, 400)
