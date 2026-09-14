"""
Root URL configuration for the EvacuSafe project (config package).
Each vertical slice (app) owns and includes its own urls.py.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.home.urls')),
    path('', include('apps.login.urls')),
    path('', include('apps.register.urls')),
    path('profile/', include('apps.profile.urls')),
    path('settings/', include('apps.user_settings.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
