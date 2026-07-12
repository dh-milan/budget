from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DocumentViewSet, DocumentTagViewSet

router = DefaultRouter()
router.register(r'documents', DocumentViewSet, basename='document')
router.register(r'tags', DocumentTagViewSet, basename='document-tag')

urlpatterns = [
    path('', include(router.urls)),
]