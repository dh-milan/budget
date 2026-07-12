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
    path('api/v1/investments/', include('apps.investments.urls')),
    path('api/v1/receipts/', include('apps.receipts.urls')),
    path('api/v1/calendar/', include('apps.financial_calendar.urls')),
    path('api/v1/family/', include('apps.family.urls')),
    path('api/v1/split-expenses/', include('apps.split_expenses.urls')),
    path('api/v1/documents/', include('apps.documents.urls')),
    path('api/v1/security/', include('apps.security.urls')),
    path('api/v1/analytics/', include('apps.analytics.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)