from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.routers import DefaultRouter
from core import api_views
from rest_framework_simplejwt.views import TokenRefreshView
from core.auth_views import CustomTokenObtainPairView, register_user
from django.contrib.auth import views as auth_views

router = DefaultRouter()
router.register(r'instances', api_views.JiraInstanceViewSet, basename='instance')
router.register(r'projects', api_views.ProjectViewSet)
router.register(r'snapshots', api_views.ConfigurationSnapshotViewSet)
router.register(r'exports', api_views.DocumentationExportViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    
    # API URLs after the web URLs
    path('api/', include((router.urls, 'api'))),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(
        template_name='swagger-ui.html'
    ), name='swagger-ui'),
    path('api/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/register/', register_user, name='register'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) 