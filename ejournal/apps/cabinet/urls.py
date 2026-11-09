from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    path("", views.dashboard, name="cabinet"),
    path("lessons/new/", views.lesson_create, name="lesson-create"),
    path("lessons/<int:pk>/", views.lesson_sheet, name="lesson-sheet"),
    path("groups/<int:pk>/report/", views.group_report, name="group-report"),
    path("login/", auth_views.LoginView.as_view(template_name="cabinet/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
]
