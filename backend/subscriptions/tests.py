from datetime import datetime
from zoneinfo import ZoneInfo
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from .models import Subscription
from .tasks import subscription_should_notify


class SchedulerIdempotencyTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='tester@example.com',
            email='tester@example.com',
            password='Passw0rd!123',
        )

    def test_same_new_york_hour_does_not_resend(self):
        ny_tz = ZoneInfo('America/New_York')
        last_sent = datetime(2026, 4, 6, 10, 5, tzinfo=ny_tz)
        now_same_hour = datetime(2026, 4, 6, 10, 45, tzinfo=ny_tz)
        sub = Subscription.objects.create(
            owner=self.user,
            ticker='AAPL',
            subscriber_email='notify@example.com',
            last_notified_time=last_sent,
        )

        with patch('subscriptions.tasks.timezone.now', return_value=now_same_hour):
            self.assertFalse(subscription_should_notify(sub))

    def test_next_new_york_hour_can_send(self):
        ny_tz = ZoneInfo('America/New_York')
        last_sent = datetime(2026, 4, 6, 10, 5, tzinfo=ny_tz)
        now_next_hour = datetime(2026, 4, 6, 11, 0, tzinfo=ny_tz)
        sub = Subscription.objects.create(
            owner=self.user,
            ticker='MSFT',
            subscriber_email='notify2@example.com',
            last_notified_time=last_sent,
        )

        with patch('subscriptions.tasks.timezone.now', return_value=now_next_hour):
            self.assertTrue(subscription_should_notify(sub))
