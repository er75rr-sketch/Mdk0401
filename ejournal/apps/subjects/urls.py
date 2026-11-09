from rest_framework.routers import SimpleRouter

from .views import SubjectViewSet, TeacherAssignmentViewSet

router = SimpleRouter()
router.register("subjects", SubjectViewSet, basename="subject")
router.register("assignments", TeacherAssignmentViewSet, basename="assignment")

urlpatterns = router.urls
