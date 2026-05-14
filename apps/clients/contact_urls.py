from rest_framework.routers import DefaultRouter

from .views import ClientContactViewSet


router = DefaultRouter()
router.register("", ClientContactViewSet, basename="client-contact")

urlpatterns = router.urls