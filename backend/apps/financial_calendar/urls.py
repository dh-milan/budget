from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import FinancialCalendarEventViewSet

router = DefaultRouter()
router.register(r'events', FinancialCalendarEventViewSet, basename='financial-calendar-event')

urlpatterns = [
    path('', include(router.urls)),
]