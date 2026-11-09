from rest_framework.routers import SimpleRouter

from .views import AttendanceViewSet, GradeViewSet, LessonViewSet

router = SimpleRouter()
router.register("lessons", LessonViewSet, basename="lesson")
router.register("grades", GradeViewSet, basename="grade")
router.register("attendance", AttendanceViewSet, basename="attendance")

urlpatterns = router.urls
