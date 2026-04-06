from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .auth_serializers import RegisterSerializer


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response(
            {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': {
                    'id': user.pk,
                    'username': user.username,
                    'email': user.email or '',
                    'is_staff': user.is_staff,
                },
            },
            status=status.HTTP_201_CREATED,
        )


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        u = request.user
        return Response(
            {
                'id': u.pk,
                'username': u.username,
                'email': u.email or u.username,
                'is_staff': bool(u.is_staff),
            },
            status=status.HTTP_200_OK,
        )


class AdminUserDeleteView(APIView):
    permission_classes = [IsAdminUser]

    def delete(self, request, user_id: int):
        if request.user.pk == user_id:
            return Response(
                {'detail': 'You cannot delete the current admin user.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        target = get_user_model().objects.filter(pk=user_id).first()
        if target is None:
            return Response({'detail': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)
        target.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AdminUserListView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        rows = (
            get_user_model()
            .objects.filter(is_staff=False)
            .order_by('username')
            .values('id', 'username', 'email', 'is_staff')
        )
        data = [
            {
                'id': r['id'],
                'username': r['username'],
                'email': r['email'] or r['username'],
                'is_staff': bool(r['is_staff']),
            }
            for r in rows
        ]
        return Response(data, status=status.HTTP_200_OK)
