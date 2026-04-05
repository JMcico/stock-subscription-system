from django.conf import settings
from django.db import models


class Subscription(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='subscriptions',
    )
    ticker = models.CharField(max_length=20, db_index=True)
    subscriber_email = models.EmailField()
    last_notified_price = models.DecimalField(
        max_digits=20,
        decimal_places=4,
        null=True,
        blank=True,
    )
    last_notified_time = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['owner', 'ticker', 'subscriber_email'],
                name='uniq_subscription_owner_ticker_subscriber_email',
            ),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.ticker} → {self.subscriber_email}'
