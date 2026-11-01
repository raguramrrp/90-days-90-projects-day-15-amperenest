from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('accounts/', include('accounts.urls')),
    path('households/', include('households.urls')),
    path('meters/', include('meters.urls')),
    path('tariffs/', include('tariffs.urls')),
    path('consumption/', include('consumption.urls')),
    path('billing/', include('billing.urls')),
    path('appliances/', include('appliances.urls')),
    path('budgets/', include('budgets.urls')),
    path('alerts/', include('alerts.urls')),
    path('analytics/', include('analytics.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
