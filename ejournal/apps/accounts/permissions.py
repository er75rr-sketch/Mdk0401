"""Общие проверки прав по ролям — используются всеми модулями."""
from rest_framework.permissions import SAFE_METHODS, BasePermission


def is_admin(user):
    return bool(user and user.is_authenticated and (user.is_superuser or getattr(user, "role", None) == "admin"))


def is_teacher(user):
    return bool(user and user.is_authenticated and getattr(user, "role", None) in ("teacher", "curator"))


def is_student(user):
    return bool(user and user.is_authenticated and getattr(user, "role", None) == "student")


class IsAdminRole(BasePermission):
    message = "Действие доступно только администратору."

    def has_permission(self, request, view):
        return is_admin(request.user)


class IsAdminOrReadOnly(BasePermission):
    """Читать могут все авторизованные, изменять — только администратор."""
    message = "Изменять данные может только администратор."

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        if request.method in SAFE_METHODS:
            return True
        return is_admin(request.user)


class IsStaffRole(BasePermission):
    """Администратор, преподаватель или куратор (не студент)."""
    message = "Раздел недоступен для студентов."

    def has_permission(self, request, view):
        return is_admin(request.user) or is_teacher(request.user)
