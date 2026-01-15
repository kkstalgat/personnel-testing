from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TestViewSet, TestSessionViewSet, TestResultViewSet

router = DefaultRouter()
router.register(r'tests', TestViewSet, basename='test')
router.register(r'sessions', TestSessionViewSet, basename='test-session')
router.register(r'results', TestResultViewSet, basename='test-result')

urlpatterns = [
    path('', include(router.urls)),
]
