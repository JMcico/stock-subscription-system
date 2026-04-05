import logging

from django.db import IntegrityError
from rest_framework import serializers

logger = logging.getLogger(__name__)

from .models import Subscription
from .utils import get_price, validate_ticker_exists


class SubscriptionSerializer(serializers.ModelSerializer):
    """Create/list subscription rows; ticker validated against Yahoo Finance (or mock rules)."""

    current_price = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Subscription
        fields = (
            'id',
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
            'current_price',
            'last_notified_price',
            'last_notified_time',
            'created_at',
            'updated_at',
        )

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
        validated_data['owner'] = self.context['request'].user
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
