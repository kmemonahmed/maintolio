from rest_framework.routers import DefaultRouter

from .views import ClientPortalWorkOrderViewSet


router = DefaultRouter()
router.register("requests", ClientPortalWorkOrderViewSet, basename="client-portal-request")

urlpatterns = router.urls