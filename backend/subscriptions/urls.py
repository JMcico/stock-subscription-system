from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import NotificationLogViewSet, SubscriptionViewSet, ValidateTickerView

router = DefaultRouter()
router.register(r'subscriptions', SubscriptionViewSet, basename='subscription')
router.register(r'notification-logs', NotificationLogViewSet, basename='notification-log')

urlpatterns = [
    path('validate_ticker/', ValidateTickerView.as_view(), name='validate-ticker'),
] + router.urls
