from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
]

# Serve static files in development
#if settings.DEBUG:
 #   urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
 #   urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
 #   urlpatterns += static(settings.STATIC_URL, document_root=settings.BASE_DIR / 'public')





    # Serve static and media files in development
if settings.DEBUG:
    # Route pour servir /assets/ directement depuis public/assets/
    urlpatterns += [
        re_path(r'^assets/(?P<path>.*)$', serve, {
            'document_root': settings.BASE_DIR / 'public' / 'assets',
        }),
    ]
    
    # Routes pour /static/ et /media/
    urlpatterns += static(settings.STATIC_URL, document_root=settings.BASE_DIR / 'public')
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
