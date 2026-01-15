from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from .views import UserViewSet, SubscriptionPlanViewSet, SubscriptionViewSet

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'subscription-plans', SubscriptionPlanViewSet, basename='subscription-plan')
router.register(r'subscriptions', SubscriptionViewSet, basename='subscription')

urlpatterns = [
    path('', include(router.urls)),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
