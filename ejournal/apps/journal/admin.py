from django.contrib import admin

from .models import Attendance, Grade, Lesson


class GradeInline(admin.TabularInline):
    model = Grade
    extra = 0
    autocomplete_fields = ("student",)
    fields = ("student", "value", "comment")


class AttendanceInline(admin.TabularInline):
    model = Attendance
    extra = 0
    autocomplete_fields = ("student",)
    fields = ("student", "status")


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ("date", "subject_name", "group_name", "topic", "lesson_type")
    list_filter = ("assignment__group", "assignment__subject", "lesson_type", "date")
    search_fields = ("topic", "assignment__subject__name")
    date_hierarchy = "date"
    inlines = [AttendanceInline, GradeInline]

    @admin.display(description="Дисциплина", ordering="assignment__subject__name")
    def subject_name(self, obj):
        return obj.assignment.subject.name

    @admin.display(description="Группа", ordering="assignment__group__name")
    def group_name(self, obj):
        return obj.assignment.group.name


@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = ("student", "value", "lesson", "created_at")
    list_filter = ("value", "student__group", "lesson__assignment__subject")
    search_fields = ("student__last_name", "lesson__topic")
    autocomplete_fields = ("student",)


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ("student", "status", "lesson")
    list_filter = ("status", "student__group", "lesson__assignment__subject")
    search_fields = ("student__last_name",)
    autocomplete_fields = ("student",)
