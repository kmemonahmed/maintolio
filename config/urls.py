from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static

from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("apps.accounts.urls")),
    path("api/organizations/", include("apps.organizations.urls")),
    path("api/team-members/", include("apps.organizations.team_urls")),
    path("api/clients/", include("apps.clients.client_urls")),
    path("api/client-contacts/", include("apps.clients.contact_urls")),
    path("api/assets/", include("apps.assets.urls")),
    path("api/work-orders/", include("apps.workorders.urls")),
    path("api/technician/", include("apps.workorders.technician_urls")),
    path("api/client-portal/", include("apps.workorders.client_portal_urls")),


    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path(
        "api/redoc/",
        SpectacularRedocView.as_view(url_name="schema"),
        name="redoc",
    ),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
