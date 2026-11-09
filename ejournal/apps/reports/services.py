"""Расчёт показателей успеваемости и посещаемости."""
from django.db.models import Avg, Count, Q

from apps.journal.models import Attendance, Grade, Lesson
from apps.students.models import Student, StudyGroup
from apps.subjects.models import Subject


def _round(value):
    return round(float(value), 2) if value is not None else None


def attendance_summary(qs):
    counts = qs.aggregate(
        total=Count("id"),
        present=Count("id", filter=Q(status=Attendance.Status.PRESENT)),
        absent=Count("id", filter=Q(status=Attendance.Status.ABSENT)),
        late=Count("id", filter=Q(status=Attendance.Status.LATE)),
        excused=Count("id", filter=Q(status=Attendance.Status.EXCUSED)),
    )
    attended = counts["present"] + counts["late"]
    counts["attendance_percent"] = round(attended * 100 / counts["total"], 1) if counts["total"] else None
    return counts


def kpi():
    grades = Grade.objects.all()
    distribution = {str(v): 0 for v in (5, 4, 3, 2)}
    for row in grades.values("value").annotate(n=Count("id")):
        distribution[str(row["value"])] = row["n"]

    underperforming = (
        Student.objects.filter(is_active=True)
        .annotate(avg=Avg("grades__value"))
        .filter(avg__lt=3)
        .count()
    )
    total_grades = grades.count()
    good = distribution["5"] + distribution["4"]
    return {
        "groups": StudyGroup.objects.count(),
        "students": Student.objects.filter(is_active=True).count(),
        "subjects": Subject.objects.count(),
        "lessons": Lesson.objects.count(),
        "grades": total_grades,
        "average_grade": _round(grades.aggregate(avg=Avg("value"))["avg"]),
        "quality_percent": round(good * 100 / total_grades, 1) if total_grades else None,
        "grades_distribution": distribution,
        "underperforming_students": underperforming,
        "attendance": attendance_summary(Attendance.objects.all()),
    }


def group_report(group):
    stats = {
        row["student"]: row
        for row in Grade.objects.filter(student__group=group)
        .values("student").annotate(avg=Avg("value"), count=Count("id"))
    }
    absences = {
        row["student"]: row["n"]
        for row in Attendance.objects.filter(student__group=group, status=Attendance.Status.ABSENT)
        .values("student").annotate(n=Count("id"))
    }
    rows = []
    for s in group.students.filter(is_active=True):
        st = stats.get(s.id, {})
        rows.append({
            "student_id": s.id,
            "student": s.full_name,
            "average_grade": _round(st.get("avg")),
            "grades_count": st.get("count", 0),
            "absences": absences.get(s.id, 0),
        })
    rows.sort(key=lambda r: (r["average_grade"] is None, -(r["average_grade"] or 0), r["student"]))
    return {
        "group": group.name,
        "course": group.course,
        "average_grade": _round(Grade.objects.filter(student__group=group).aggregate(a=Avg("value"))["a"]),
        "attendance": attendance_summary(Attendance.objects.filter(student__group=group)),
        "students": rows,
    }


def student_report(student):
    subjects = (
        Grade.objects.filter(student=student)
        .values("lesson__assignment__subject__name")
        .annotate(avg=Avg("value"), count=Count("id"))
        .order_by("lesson__assignment__subject__name")
    )
    return {
        "student": student.full_name,
        "group": student.group.name,
        "average_grade": _round(Grade.objects.filter(student=student).aggregate(a=Avg("value"))["a"]),
        "attendance": attendance_summary(Attendance.objects.filter(student=student)),
        "subjects": [
            {
                "subject": row["lesson__assignment__subject__name"],
                "average_grade": _round(row["avg"]),
                "grades_count": row["count"],
            }
            for row in subjects
        ],
    }
