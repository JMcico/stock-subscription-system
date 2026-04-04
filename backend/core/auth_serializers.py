from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import validate_email
from rest_framework import serializers


class RegisterSerializer(serializers.ModelSerializer):
    """
    Regular users sign up with email as `username` (validated as email format).
    `User.email` is set to the same value for consistency with the rest of the app.
    """

    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ('username', 'password')

    def validate_password(self, value):
        validate_password(value)
        return value

    def validate_username(self, value):
        normalized = (value or '').strip().lower()
        if not normalized:
            raise serializers.ValidationError('This field may not be blank.')
        try:
            validate_email(normalized)
        except DjangoValidationError:
            raise serializers.ValidationError('Enter a valid email address.')
        if User.objects.filter(username__iexact=normalized).exists():
            raise serializers.ValidationError('A user with this email already exists.')
        if User.objects.filter(email__iexact=normalized).exists():
            raise serializers.ValidationError('A user with this email already exists.')
        return normalized

    def create(self, validated_data):
        u = validated_data['username']
        return User.objects.create_user(
            username=u,
            password=validated_data['password'],
            email=u,
            is_staff=False,
            is_superuser=False,
        )
