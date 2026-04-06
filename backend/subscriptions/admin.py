from django.contrib import admin

from .models import NotificationLog, Subscription


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'ticker',
        'subscriber_email',
        'owner',
        'last_notified_price',
        'last_notified_time',
        'created_at',
    )
    list_filter = ('created_at',)
    search_fields = ('ticker', 'subscriber_email', 'owner__username')
    raw_id_fields = ('owner',)


@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'owner',
        'recipient_email',
        'tickers_summary',
        'status',
        'created_at',
    )
    list_filter = ('status', 'created_at')
    search_fields = ('recipient_email', 'tickers_summary', 'owner__username', 'owner__email')
    raw_id_fields = ('owner',)
