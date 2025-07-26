from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

urlpatterns = [
    path('admin/', admin.site.urls),  # functionality for the admin panel is not described
    path('api/schema/', SpectacularAPIView.as_view(), name='api-schema'),
    path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='api-schema'), name='swagger-ui'),
    path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='api-schema'), name='redoc'),
    path('api/', include('api.urls', namespace='api')),
]
