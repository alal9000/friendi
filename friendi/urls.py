from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings

from app.sitemaps import StaticViewSitemap

# if settings.DEBUG:
#     import debug_toolbar

sitemaps = {
    'static': StaticViewSitemap
}

urlpatterns = [
    # path('__debug__/', include(debug_toolbar.urls)),
    path('', include('app.urls')),
    path('accounts/', include('allauth.urls')),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}),
    path('admin/', admin.site.urls),
    path('photos/', include('photos.urls')),
    path('friends/', include('friends.urls')),
    path('notifications/', include('notifications.urls')),
    path('direct_messages/', include('direct_messages.urls')),
    path('events/', include('events.urls')),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
