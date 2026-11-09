from django.db.models import Q
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import SAFE_METHODS, BasePermission
from rest_framework.response import Response

from apps.accounts.permissions import is_admin, is_student, is_teacher

from .models import Attendance, Grade, Lesson
from .serializers import AttendanceSerializer, GradeSerializer, LessonSerializer


def _assignment_of(obj):
    return obj.assignment if isinstance(obj, Lesson) else obj.lesson.assignment


class JournalPermission(BasePermission):
    """Читать — все авторизованные (в пределах своих данных).
    Изменять — администратор или преподаватель, который ведёт эту дисциплину."""
    message = "Изменять журнал может только преподаватель этой дисциплины или администратор."

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        if request.method in SAFE_METHODS:
            return True
        return is_admin(request.user) or is_teacher(request.user)

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS or is_admin(request.user):
            return True
        return _assignment_of(obj).teacher_id == request.user.id


def _check_own_assignment(user, assignment):
    if not is_admin(user) and assignment.teacher_id != user.id:
        raise PermissionDenied("Можно работать только со своими дисциплинами (своей нагрузкой).")


class LessonViewSet(viewsets.ModelViewSet):
    """Занятия. Фильтры: ?group=, ?subject=, ?assignment=, ?date_from=, ?date_to="""
    serializer_class = LessonSerializer
    permission_classes = [JournalPermission]

    def get_queryset(self):
        qs = Lesson.objects.select_related("assignment__subject", "assignment__group", "assignment__teacher")
        user = self.request.user
        if is_teacher(user):
            qs = qs.filter(Q(assignment__teacher=user) | Q(assignment__group__curator=user))
        elif is_student(user):
            qs = qs.filter(assignment__group__students__user=user)
        params = self.request.query_params
        filters = {
            "group": "assignment__group_id",
            "subject": "assignment__subject_id",
            "assignment": "assignment_id",
            "date_from": "date__gte",
            "date_to": "date__lte",
        }
        for param, lookup in filters.items():
            if params.get(param):
                qs = qs.filter(**{lookup: params[param]})
        return qs.distinct()

    def perform_create(self, serializer):
        _check_own_assignment(self.request.user, serializer.validated_data["assignment"])
        serializer.save()

    def perform_update(self, serializer):
        assignment = serializer.validated_data.get("assignment", serializer.instance.assignment)
        _check_own_assignment(self.request.user, assignment)
        serializer.save()

    @action(detail=True, methods=["get"])
    def sheet(self, request, pk=None):
        """GET /api/lessons/{id}/sheet/ — ведомость занятия: студенты группы, оценки, посещаемость."""
        lesson = self.get_object()
        grades = {g.student_id: g.value for g in lesson.grades.all()}
        marks = {a.student_id: a.get_status_display() for a in lesson.attendance.all()}
        students = lesson.assignment.group.students.filter(is_active=True)
        if is_student(request.user):
            students = students.filter(user=request.user)
        rows = [
            {
                "student_id": s.id,
                "student": s.full_name,
                "grade": grades.get(s.id),
                "attendance": marks.get(s.id),
            }
            for s in students
        ]
        return Response({"lesson": LessonSerializer(lesson).data, "students": rows})


class _LessonChildViewSet(viewsets.ModelViewSet):
    """Общая логика для оценок и посещаемости."""
    permission_classes = [JournalPermission]
    model = None

    def get_queryset(self):
        qs = self.model.objects.select_related(
            "student", "lesson__assignment__subject", "lesson__assignment__group"
        )
        user = self.request.user
        if is_teacher(user):
            qs = qs.filter(Q(lesson__assignment__teacher=user) | Q(lesson__assignment__group__curator=user))
        elif is_student(user):
            qs = qs.filter(student__user=user)
        params = self.request.query_params
        filters = {
            "lesson": "lesson_id",
            "student": "student_id",
            "group": "student__group_id",
            "subject": "lesson__assignment__subject_id",
        }
        for param, lookup in filters.items():
            if params.get(param):
                qs = qs.filter(**{lookup: params[param]})
        return qs.distinct()

    def perform_create(self, serializer):
        _check_own_assignment(self.request.user, serializer.validated_data["lesson"].assignment)
        serializer.save()

    def perform_update(self, serializer):
        lesson = serializer.validated_data.get("lesson", serializer.instance.lesson)
        _check_own_assignment(self.request.user, lesson.assignment)
        serializer.save()


class GradeViewSet(_LessonChildViewSet):
    """Оценки. Фильтры: ?lesson=, ?student=, ?group=, ?subject="""
    model = Grade
    serializer_class = GradeSerializer


class AttendanceViewSet(_LessonChildViewSet):
    """Посещаемость. Фильтры: ?lesson=, ?student=, ?group=, ?subject="""
    model = Attendance
    serializer_class = AttendanceSerializer
