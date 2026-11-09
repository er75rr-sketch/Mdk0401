"""Веб-страницы: кабинет студента и рабочее место преподавателя."""
from collections import OrderedDict

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Avg, Count
from django.shortcuts import get_object_or_404, redirect, render

from apps.accounts.permissions import is_admin, is_student, is_teacher
from apps.journal.models import Attendance, Grade, Lesson
from apps.reports import services
from apps.students.models import StudyGroup
from apps.subjects.models import TeacherAssignment

from .forms import LessonForm

GRADE_VALUES = ("5", "4", "3", "2")


@login_required
def dashboard(request):
    user = request.user
    if is_admin(user):
        return redirect("/admin/")
    if is_teacher(user):
        return teacher_dashboard(request)
    if is_student(user):
        return student_dashboard(request)
    raise PermissionDenied


# ---------------------------------------------------------------- студент

def student_dashboard(request):
    student = getattr(request.user, "student_profile", None)
    if student is None:
        return render(request, "cabinet/no_profile.html")

    subjects = OrderedDict()
    for a in student.group.assignments.select_related("subject", "teacher").order_by("subject__name"):
        subjects[a.subject_id] = {"name": a.subject.name, "teacher": a.teacher.full_name, "grades": [], "avg": None}

    grades = Grade.objects.filter(student=student).select_related("lesson__assignment__subject").order_by("lesson__date")
    for g in grades:
        sid = g.lesson.assignment.subject_id
        if sid in subjects:
            subjects[sid]["grades"].append(g)
    for item in subjects.values():
        values = [g.value for g in item["grades"]]
        item["avg"] = round(sum(values) / len(values), 2) if values else None

    grade_by_lesson = {g.lesson_id: g.value for g in grades}
    mark_by_lesson = {a.lesson_id: a for a in Attendance.objects.filter(student=student)}
    recent = []
    lessons = (
        Lesson.objects.filter(assignment__group=student.group)
        .select_related("assignment__subject")
        .order_by("-date", "-id")[:15]
    )
    for lesson in lessons:
        mark = mark_by_lesson.get(lesson.id)
        recent.append({
            "lesson": lesson,
            "grade": grade_by_lesson.get(lesson.id),
            "status": mark.status if mark else None,
            "status_display": mark.get_status_display() if mark else "—",
        })

    report = services.student_report(student)
    return render(request, "cabinet/dashboard.html", {
        "student": student,
        "subjects": subjects.values(),
        "recent": recent,
        "average": report["average_grade"],
        "attendance": report["attendance"],
    })


# ---------------------------------------------------------- преподаватель

def teacher_dashboard(request):
    user = request.user
    assignments = (
        TeacherAssignment.objects.filter(teacher=user)
        .select_related("subject", "group")
        .annotate(lessons_count=Count("lessons", distinct=True), avg=Avg("lessons__grades__value"))
        .order_by("group__name", "subject__name")
    )
    recent = (
        Lesson.objects.filter(assignment__teacher=user)
        .select_related("assignment__subject", "assignment__group")
        .annotate(grades_count=Count("grades", distinct=True))
        .order_by("-date", "-id")[:10]
    )
    curated = StudyGroup.objects.filter(curator=user).order_by("name")
    return render(request, "cabinet/teacher_dashboard.html", {
        "assignments": assignments, "recent": recent, "curated": curated,
    })


def _can_edit(user, lesson):
    return is_admin(user) or lesson.assignment.teacher_id == user.id


def _can_view(user, lesson):
    return _can_edit(user, lesson) or lesson.assignment.group.curator_id == user.id


@login_required
def lesson_create(request):
    if not (is_teacher(request.user) or is_admin(request.user)):
        raise PermissionDenied
    teacher = None if is_admin(request.user) else request.user
    initial = {}
    if request.GET.get("assignment"):
        initial["assignment"] = request.GET["assignment"]
    form = LessonForm(request.POST or None, teacher=teacher, initial=initial)
    if request.method == "POST" and form.is_valid():
        lesson = form.save()
        messages.success(request, "Занятие создано. Отметьте посещаемость и оценки.")
        return redirect("lesson-sheet", pk=lesson.pk)
    return render(request, "cabinet/lesson_form.html", {"form": form})


@login_required
def lesson_sheet(request, pk):
    lesson = get_object_or_404(
        Lesson.objects.select_related("assignment__subject", "assignment__group", "assignment__teacher"), pk=pk
    )
    if not _can_view(request.user, lesson):
        raise PermissionDenied
    can_edit = _can_edit(request.user, lesson)
    students = list(lesson.assignment.group.students.filter(is_active=True))

    if request.method == "POST":
        if not can_edit:
            raise PermissionDenied
        errors = _save_sheet(request.POST, lesson, students)
        for e in errors:
            messages.error(request, e)
        if not errors:
            messages.success(request, "Ведомость сохранена.")
        return redirect("lesson-sheet", pk=lesson.pk)

    grades = {g.student_id: g.value for g in lesson.grades.all()}
    marks = {a.student_id: a.status for a in lesson.attendance.all()}
    rows = [{"student": s, "grade": grades.get(s.id), "status": marks.get(s.id, "")} for s in students]
    return render(request, "cabinet/lesson_sheet.html", {
        "lesson": lesson, "rows": rows, "can_edit": can_edit,
        "statuses": Attendance.Status.choices, "grade_values": GRADE_VALUES,
    })


@transaction.atomic
def _save_sheet(data, lesson, students):
    """Сохраняет посещаемость и оценки по всей группе. Возвращает список ошибок."""
    errors = []
    valid_statuses = dict(Attendance.Status.choices)
    for s in students:
        status = data.get(f"att_{s.id}", "")
        grade = data.get(f"grade_{s.id}", "")
        if status not in valid_statuses:
            status = ""
        if grade not in GRADE_VALUES:
            grade = ""
        if status == Attendance.Status.ABSENT and grade:
            errors.append(f"{s.full_name}: нельзя одновременно отметить «н» и поставить оценку — строка не сохранена.")
            continue

        if not grade:
            Grade.objects.filter(lesson=lesson, student=s).delete()
        if status:
            Attendance.objects.update_or_create(lesson=lesson, student=s, defaults={"status": status})
        elif not grade:
            Attendance.objects.filter(lesson=lesson, student=s).delete()
        if grade:
            Grade.objects.update_or_create(lesson=lesson, student=s, defaults={"value": int(grade)})
    return errors


@login_required
def group_report(request, pk):
    group = get_object_or_404(StudyGroup, pk=pk)
    user = request.user
    allowed = (
        is_admin(user) or group.curator_id == user.id
        or TeacherAssignment.objects.filter(group=group, teacher=user).exists()
    )
    if not allowed:
        raise PermissionDenied
    return render(request, "cabinet/group_report.html", {"report": services.group_report(group), "group": group})
