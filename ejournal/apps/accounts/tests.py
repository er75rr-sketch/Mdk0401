from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

User = get_user_model()


class AuthTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="teacher", password="Teacher12345", role="teacher",
            last_name="Петрова", first_name="Анна",
        )

    def test_login_returns_jwt_and_user(self):
        resp = self.client.post("/api/auth/login/", {"username": "teacher", "password": "Teacher12345"})
        self.assertEqual(resp.status_code, 200)
        self.assertIn("access", resp.data)
        self.assertIn("refresh", resp.data)
        self.assertEqual(resp.data["user"]["role"], "teacher")

    def test_wrong_password(self):
        resp = self.client.post("/api/auth/login/", {"username": "teacher", "password": "wrong"})
        self.assertEqual(resp.status_code, 401)

    def test_me_with_token(self):
        token = self.client.post(
            "/api/auth/login/", {"username": "teacher", "password": "Teacher12345"}
        ).data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        resp = self.client.get("/api/auth/me/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["full_name"], "Петрова Анна")

    def test_me_without_token(self):
        self.assertEqual(self.client.get("/api/auth/me/").status_code, 401)

    def test_refresh(self):
        refresh = self.client.post(
            "/api/auth/login/", {"username": "teacher", "password": "Teacher12345"}
        ).data["refresh"]
        resp = self.client.post("/api/auth/refresh/", {"refresh": refresh})
        self.assertEqual(resp.status_code, 200)
        self.assertIn("access", resp.data)

    def test_teacher_cannot_manage_users(self):
        self.client.force_authenticate(self.user)
        self.assertEqual(self.client.get("/api/users/").status_code, 403)

    def test_superuser_gets_admin_role(self):
        admin = User.objects.create_superuser("root", "root@example.com", "Root12345")
        self.assertEqual(admin.role, "admin")
