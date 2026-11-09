from rest_framework.routers import SimpleRouter

from .views import StudentViewSet, StudyGroupViewSet

router = SimpleRouter()
router.register("groups", StudyGroupViewSet, basename="group")
router.register("students", StudentViewSet, basename="student")

urlpatterns = router.urls
