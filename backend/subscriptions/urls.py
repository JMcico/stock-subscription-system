from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import SubscriptionViewSet, ValidateTickerView

router = DefaultRouter()
router.register(r'subscriptions', SubscriptionViewSet, basename='subscription')

urlpatterns = [
    path('validate_ticker/', ValidateTickerView.as_view(), name='validate-ticker'),
] + router.urls
