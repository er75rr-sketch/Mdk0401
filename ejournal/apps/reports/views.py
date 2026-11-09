from django.shortcuts import get_object_or_404
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import IsStaffRole, is_student
from apps.students.models import Student, StudyGroup

from . import services


class KPIView(APIView):
    """GET /api/reports/kpi/ — сводные показатели по колледжу."""
    permission_classes = [IsStaffRole]

    def get(self, request):
        return Response(services.kpi())


class GroupReportView(APIView):
    """GET /api/reports/groups/{id}/ — успеваемость и пропуски группы."""
    permission_classes = [IsStaffRole]

    def get(self, request, pk):
        group = get_object_or_404(StudyGroup, pk=pk)
        return Response(services.group_report(group))


class StudentReportView(APIView):
    """GET /api/reports/students/{id}/ — средние баллы студента по дисциплинам.
    Студент может смотреть только свой отчёт."""
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        student = get_object_or_404(Student.objects.select_related("group"), pk=pk)
        if is_student(request.user) and student.user_id != request.user.id:
            raise PermissionDenied("Можно смотреть только свой отчёт.")
        return Response(services.student_report(student))
