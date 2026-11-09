from django.contrib import admin

from .models import Subject, TeacherAssignment


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "hours")
    search_fields = ("code", "name")


@admin.register(TeacherAssignment)
class TeacherAssignmentAdmin(admin.ModelAdmin):
    list_display = ("subject", "group", "teacher")
    list_filter = ("group", "subject", "teacher")
    search_fields = ("subject__name", "group__name", "teacher__last_name")
