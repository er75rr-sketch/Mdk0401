from django import forms

from apps.journal.models import Lesson
from apps.subjects.models import TeacherAssignment


class LessonForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = ["assignment", "date", "topic", "lesson_type"]
        widgets = {"date": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d")}

    def __init__(self, *args, teacher=None, **kwargs):
        super().__init__(*args, **kwargs)
        qs = TeacherAssignment.objects.select_related("subject", "group")
        if teacher is not None:
            qs = qs.filter(teacher=teacher)
        self.fields["assignment"].queryset = qs
        self.fields["assignment"].label_from_instance = lambda a: f"{a.subject.name} — {a.group.name}"
