from rest_framework import serializers

from .models import Student, StudyGroup


class StudyGroupSerializer(serializers.ModelSerializer):
    students_count = serializers.IntegerField(read_only=True)
    curator_name = serializers.CharField(source="curator.full_name", read_only=True, default=None)

    class Meta:
        model = StudyGroup
        fields = ["id", "name", "course", "specialty", "curator", "curator_name", "students_count"]


class StudentSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(read_only=True)
    group_name = serializers.CharField(source="group.name", read_only=True)

    class Meta:
        model = Student
        fields = [
            "id", "last_name", "first_name", "middle_name", "full_name", "group", "group_name",
            "record_book", "birth_date", "email", "is_active", "user",
        ]
