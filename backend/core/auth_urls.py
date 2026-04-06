from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .auth_views import AdminUserDeleteView, AdminUserListView, MeView, RegisterView

urlpatterns = [
    path('auth/register/', RegisterView.as_view(), name='auth-register'),
    path('auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/me/', MeView.as_view(), name='auth-me'),
    path('auth/users/', AdminUserListView.as_view(), name='auth-user-list'),
    path('auth/users/<int:user_id>/', AdminUserDeleteView.as_view(), name='auth-user-delete'),
]
