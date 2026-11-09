from django.db.models import Count, Q
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.accounts.permissions import IsAdminOrReadOnly, is_student

from .models import Student, StudyGroup
from .serializers import StudentSerializer, StudyGroupSerializer


class StudyGroupViewSet(viewsets.ModelViewSet):
    """Группы: читать — все, изменять — администратор. Фильтр: ?course=2"""
    serializer_class = StudyGroupSerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        qs = StudyGroup.objects.select_related("curator").annotate(
            students_count=Count("students", filter=Q(students__is_active=True))
        )
        user = self.request.user
        if is_student(user):
            qs = qs.filter(students__user=user)
        course = self.request.query_params.get("course")
        if course:
            qs = qs.filter(course=course)
        return qs.order_by("course", "name")

    @action(detail=True, methods=["get"])
    def students(self, request, pk=None):
        """GET /api/groups/{id}/students/ — список студентов группы."""
        group = self.get_object()
        qs = group.students.filter(is_active=True)
        return Response(StudentSerializer(qs, many=True).data)


class StudentViewSet(viewsets.ModelViewSet):
    """Студенты. Фильтры: ?group=1, ?search=Иван"""
    serializer_class = StudentSerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        qs = Student.objects.select_related("group")
        user = self.request.user
        if is_student(user):
            return qs.filter(user=user)
        group = self.request.query_params.get("group")
        if group:
            qs = qs.filter(group_id=group)
        search = self.request.query_params.get("search")
        if search:
            qs = qs.filter(
                Q(last_name__icontains=search) | Q(first_name__icontains=search)
                | Q(record_book__icontains=search)
            )
        return qs
