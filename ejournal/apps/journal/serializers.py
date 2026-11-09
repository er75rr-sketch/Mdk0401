from rest_framework import serializers

from .models import Attendance, Grade, Lesson, student_lesson_error


class LessonSerializer(serializers.ModelSerializer):
    subject_name = serializers.CharField(source="assignment.subject.name", read_only=True)
    group_name = serializers.CharField(source="assignment.group.name", read_only=True)
    teacher_name = serializers.CharField(source="assignment.teacher.full_name", read_only=True)
    lesson_type_display = serializers.CharField(source="get_lesson_type_display", read_only=True)

    class Meta:
        model = Lesson
        fields = [
            "id", "assignment", "subject_name", "group_name", "teacher_name",
            "date", "topic", "lesson_type", "lesson_type_display",
        ]


class _LessonStudentMixin:
    """Общая проверка: студент из группы занятия."""

    def _lesson_and_student(self, attrs):
        lesson = attrs.get("lesson", getattr(self.instance, "lesson", None))
        student = attrs.get("student", getattr(self.instance, "student", None))
        if lesson and student:
            error = student_lesson_error(student, lesson)
            if error:
                raise serializers.ValidationError({"student": error})
        return lesson, student


class GradeSerializer(_LessonStudentMixin, serializers.ModelSerializer):
    student_name = serializers.CharField(source="student.full_name", read_only=True)
    subject_name = serializers.CharField(source="lesson.assignment.subject.name", read_only=True)
    date = serializers.DateField(source="lesson.date", read_only=True)

    class Meta:
        model = Grade
        fields = ["id", "lesson", "date", "subject_name", "student", "student_name", "value", "comment", "created_at"]
        read_only_fields = ["created_at"]

    def validate(self, attrs):
        lesson, student = self._lesson_and_student(attrs)
        if lesson and student and Attendance.objects.filter(
            lesson=lesson, student=student, status=Attendance.Status.ABSENT
        ).exists():
            raise serializers.ValidationError(
                {"value": "Нельзя поставить оценку студенту, отмеченному как отсутствующий."}
            )
        return attrs


class AttendanceSerializer(_LessonStudentMixin, serializers.ModelSerializer):
    student_name = serializers.CharField(source="student.full_name", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Attendance
        fields = ["id", "lesson", "student", "student_name", "status", "status_display"]

    def validate(self, attrs):
        lesson, student = self._lesson_and_student(attrs)
        status = attrs.get("status", getattr(self.instance, "status", None))
        if lesson and student and status == Attendance.Status.ABSENT and Grade.objects.filter(
            lesson=lesson, student=student
        ).exists():
            raise serializers.ValidationError(
                {"status": "У студента есть оценка за это занятие — он не может быть отсутствующим."}
            )
        return attrs
