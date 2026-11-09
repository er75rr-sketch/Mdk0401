"""Корневые маршруты: админка, REST API, авторизация, отчёты."""
from django.contrib import admin
from django.urls import include, path
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.reverse import reverse

admin.site.site_header = "Электронный журнал"
admin.site.site_title = "Электронный журнал"
admin.site.index_title = "Администрирование"


@api_view(["GET"])
@permission_classes([AllowAny])
def api_root(request, format=None):
    """Список всех эндпоинтов API."""
    def r(name):
        return reverse(name, request=request, format=format)

    return Response({
        "auth": {
            "login": r("auth-login"),
            "refresh": r("auth-refresh"),
            "me": r("auth-me"),
        },
        "users": r("user-list"),
        "groups": r("group-list"),
        "students": r("student-list"),
        "subjects": r("subject-list"),
        "assignments": r("assignment-list"),
        "lessons": r("lesson-list"),
        "grades": r("grade-list"),
        "attendance": r("attendance-list"),
        "reports": {
            "kpi": r("report-kpi"),
            "group": request.build_absolute_uri("/api/reports/groups/{id}/"),
            "student": request.build_absolute_uri("/api/reports/students/{id}/"),
        },
    })


urlpatterns = [
    path("", include("apps.cabinet.urls")),
    path("admin/", admin.site.urls),
    path("api/", api_root, name="api-root"),
    path("api/auth/", include("apps.accounts.auth_urls")),
    path("api/reports/", include("apps.reports.urls")),
    path("api/", include("apps.accounts.urls")),
    path("api/", include("apps.students.urls")),
    path("api/", include("apps.subjects.urls")),
    path("api/", include("apps.journal.urls")),
    path("api-auth/", include("rest_framework.urls")),
]
