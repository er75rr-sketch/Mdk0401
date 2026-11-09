from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from .models import Student, StudyGroup

User = get_user_model()


class StudentsApiTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(username="adm", password="Admin12345", role="admin")
        self.teacher = User.objects.create_user(username="t1", password="Teacher12345", role="teacher")
        self.group = StudyGroup.objects.create(name="ИС-21", course=2)
        Student.objects.create(last_name="Иванов", first_name="Иван", group=self.group, record_book="21-001")
        Student.objects.create(last_name="Смирнова", first_name="Ольга", group=self.group, record_book="21-002")

    def test_admin_creates_group(self):
        self.client.force_authenticate(self.admin)
        resp = self.client.post("/api/groups/", {"name": "ИС-22", "course": 1})
        self.assertEqual(resp.status_code, 201)

    def test_teacher_cannot_create_group(self):
        self.client.force_authenticate(self.teacher)
        resp = self.client.post("/api/groups/", {"name": "ИС-23", "course": 1})
        self.assertEqual(resp.status_code, 403)

    def test_group_list_has_students_count(self):
        self.client.force_authenticate(self.teacher)
        resp = self.client.get("/api/groups/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["count"], 1)
        self.assertEqual(resp.data["results"][0]["students_count"], 2)

    def test_search_student(self):
        self.client.force_authenticate(self.teacher)
        resp = self.client.get("/api/students/", {"search": "Смир"})
        self.assertEqual(resp.data["count"], 1)

    def test_group_students_action(self):
        self.client.force_authenticate(self.teacher)
        resp = self.client.get(f"/api/groups/{self.group.id}/students/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data), 2)

    def test_anonymous_denied(self):
        self.assertEqual(self.client.get("/api/students/").status_code, 401)
