from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # API endpoints
    path('api/v1/auth/', include('apps.authentication.urls')),
    path('api/v1/ledger/', include('apps.ledger.urls')),
    path('api/v1/budgeting/', include('apps.budgeting.urls')),
    path('api/v1/bills/', include('apps.bills.urls')),
    path('api/v1/payments/', include('apps.payments.urls')),
    path('api/v1/ai/', include('apps.ai_copilot.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)