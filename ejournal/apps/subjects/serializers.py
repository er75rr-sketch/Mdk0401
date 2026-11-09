from rest_framework import serializers

from .models import Subject, TeacherAssignment


class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = ["id", "code", "name", "hours"]


class TeacherAssignmentSerializer(serializers.ModelSerializer):
    subject_name = serializers.CharField(source="subject.name", read_only=True)
    group_name = serializers.CharField(source="group.name", read_only=True)
    teacher_name = serializers.CharField(source="teacher.full_name", read_only=True)

    class Meta:
        model = TeacherAssignment
        fields = ["id", "teacher", "teacher_name", "subject", "subject_name", "group", "group_name"]

    def validate_teacher(self, teacher):
        if teacher.role not in ("teacher", "curator"):
            raise serializers.ValidationError("Нагрузку можно назначить только преподавателю или куратору.")
        return teacher
