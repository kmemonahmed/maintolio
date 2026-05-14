from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import AssetViewSet, ClientAssetListView


router = DefaultRouter()
router.register("", AssetViewSet, basename="asset")

urlpatterns = [
    path(
        "by-client/<uuid:client_id>/",
        ClientAssetListView.as_view(),
        name="assets_by_client",
    ),
]

urlpatterns += router.urls