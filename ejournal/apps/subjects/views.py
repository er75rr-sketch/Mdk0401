from rest_framework import viewsets

from apps.accounts.permissions import IsAdminOrReadOnly, is_student, is_teacher

from .models import Subject, TeacherAssignment
from .serializers import SubjectSerializer, TeacherAssignmentSerializer


class SubjectViewSet(viewsets.ModelViewSet):
    queryset = Subject.objects.all()
    serializer_class = SubjectSerializer
    permission_classes = [IsAdminOrReadOnly]


class TeacherAssignmentViewSet(viewsets.ModelViewSet):
    """Нагрузка. Преподаватель видит свою, студент — нагрузку своей группы. Фильтры: ?group=, ?teacher="""
    serializer_class = TeacherAssignmentSerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        qs = TeacherAssignment.objects.select_related("teacher", "subject", "group")
        user = self.request.user
        if is_teacher(user):
            qs = qs.filter(teacher=user)
        elif is_student(user):
            qs = qs.filter(group__students__user=user)
        for param in ("group", "teacher", "subject"):
            value = self.request.query_params.get(param)
            if value:
                qs = qs.filter(**{f"{param}_id": value})
        return qs
