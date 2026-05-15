from rest_framework.routers import DefaultRouter

from .views import TechnicianWorkOrderViewSet


router = DefaultRouter()
router.register("work-orders", TechnicianWorkOrderViewSet, basename="technician-work-order")

urlpatterns = router.urls