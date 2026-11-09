from django.urls import path

from .views import GroupReportView, KPIView, StudentReportView

urlpatterns = [
    path("kpi/", KPIView.as_view(), name="report-kpi"),
    path("groups/<int:pk>/", GroupReportView.as_view(), name="report-group"),
    path("students/<int:pk>/", StudentReportView.as_view(), name="report-student"),
]
