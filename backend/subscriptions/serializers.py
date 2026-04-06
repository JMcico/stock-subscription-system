import logging

from django.contrib.auth import get_user_model
from django.db import IntegrityError
from rest_framework import serializers

logger = logging.getLogger(__name__)

from .models import NotificationLog, Subscription
from .utils import get_price, validate_ticker_exists


class SubscriptionSerializer(serializers.ModelSerializer):
    """Create/list subscription rows; ticker validated against Yahoo Finance (or mock rules)."""

    current_price = serializers.SerializerMethodField(read_only=True)
    owner = serializers.SerializerMethodField(read_only=True)
    owner_id = serializers.IntegerField(read_only=True)
    target_owner_id = serializers.IntegerField(write_only=True, required=False)

    class Meta:
        model = Subscription
        fields = (
            'id',
            'owner',
            'owner_id',
            'target_owner_id',
            'ticker',
            'subscriber_email',
            'current_price',
            'last_notified_price',
            'last_notified_time',
            'created_at',
            'updated_at',
        )
        read_only_fields = (
            'id',
            'owner',
            'owner_id',
            'current_price',
            'last_notified_price',
            'last_notified_time',
            'created_at',
            'updated_at',
        )

    def get_owner(self, obj):
        owner = getattr(obj, 'owner', None)
        if owner is None:
            return None
        return owner.email or owner.username

    def get_current_price(self, obj):
        try:
            return str(get_price(obj.ticker))
        except Exception as exc:
            logger.warning('get_price failed for %s: %s', obj.ticker, exc)
            return None

    def validate_ticker(self, value):
        try:
            return validate_ticker_exists(value)
        except ValueError as e:
            raise serializers.ValidationError(str(e)) from e

    def validate_subscriber_email(self, value):
        return value.strip().lower()

    def create(self, validated_data):
        request = self.context['request']
        target_owner_id = validated_data.pop('target_owner_id', None)
        if request.user.is_staff and target_owner_id:
            owner = get_user_model().objects.filter(pk=target_owner_id).first()
            if owner is None:
                raise serializers.ValidationError({'target_owner_id': ['User not found.']})
            validated_data['owner'] = owner
        else:
            validated_data['owner'] = request.user
        try:
            return Subscription.objects.create(**validated_data)
        except IntegrityError:
            raise serializers.ValidationError(
                {
                    'non_field_errors': [
                        'You already have a subscription for this ticker and email address.'
                    ]
                }
            ) from None


class NotificationLogSerializer(serializers.ModelSerializer):
    owner = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = NotificationLog
        fields = (
            'id',
            'owner',
            'tickers_summary',
            'recipient_email',
            'status',
            'created_at',
        )
        read_only_fields = fields

    def get_owner(self, obj):
        owner = getattr(obj, 'owner', None)
        if owner is None:
            return None
        return owner.email or owner.username

    def update(self, instance, validated_data):
        try:
            return super().update(instance, validated_data)
        except IntegrityError:
            raise serializers.ValidationError(
                {
                    'non_field_errors': [
                        'You already have a subscription for this ticker and email address.'
                    ]
                }
            ) from None
