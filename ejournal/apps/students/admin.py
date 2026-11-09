from django.contrib import admin

from .models import Student, StudyGroup


class StudentInline(admin.TabularInline):
    model = Student
    extra = 0
    fields = ("last_name", "first_name", "middle_name", "record_book", "is_active")
    show_change_link = True


@admin.register(StudyGroup)
class StudyGroupAdmin(admin.ModelAdmin):
    list_display = ("name", "course", "specialty", "curator", "students_total")
    list_filter = ("course",)
    search_fields = ("name", "specialty")
    inlines = [StudentInline]

    @admin.display(description="Студентов")
    def students_total(self, obj):
        return obj.students.filter(is_active=True).count()


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ("last_name", "first_name", "middle_name", "group", "record_book", "is_active")
    list_filter = ("group", "group__course", "is_active")
    search_fields = ("last_name", "first_name", "record_book")
    autocomplete_fields = ("user",)
