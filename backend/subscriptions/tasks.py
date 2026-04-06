"""
Django-Q2 scheduled tasks (US market hours, merged subscription emails).
"""

from __future__ import annotations

import logging
from collections import defaultdict
from zoneinfo import ZoneInfo

from django.contrib.auth import get_user_model
from django.utils import timezone

from .models import Subscription
from .services import send_subscription_emails

logger = logging.getLogger(__name__)

NY_TZ = ZoneInfo('America/New_York')


def _is_us_market_hours() -> bool:
    """Mon–Fri, 09:00–17:00 America/New_York (inclusive hour)."""
    now_ny = timezone.now().astimezone(NY_TZ)
    if now_ny.weekday() >= 5:
        return False
    return 9 <= now_ny.hour <= 17


def _same_ny_clock_hour(a, b) -> bool:
    """True if both datetimes fall in the same calendar hour in America/New_York."""
    ta = a.astimezone(NY_TZ)
    tb = b.astimezone(NY_TZ)
    return (ta.year, ta.month, ta.day, ta.hour) == (tb.year, tb.month, tb.day, tb.hour)


def subscription_should_notify(sub: Subscription) -> bool:
    """
    Cadence is by NY clock hours (9, 10, …), not rolling 60 minutes from last_notified_time.
    Eligible only on first send or when entering a new NY hour since last send.
    """
    if sub.last_notified_time is None:
        return True
    if not _same_ny_clock_hour(timezone.now(), sub.last_notified_time):
        return True
    return False


def run_hourly_checks() -> dict:
    """
    Entry point for Django-Q hourly schedule.
    Runs only during US market hours; at most one send per subscription per NY clock hour
    and sends merged emails per owner via send_subscription_emails.
    """
    if not _is_us_market_hours():
        logger.info('run_hourly_checks: outside US market hours (America/New_York), skip')
        return {'status': 'skipped', 'reason': 'outside_market_hours'}

    eligible_ids: list[int] = []
    qs = Subscription.objects.select_related('owner').filter(owner__is_active=True)
    for sub in qs.iterator():
        if subscription_should_notify(sub):
            eligible_ids.append(sub.pk)

    if not eligible_ids:
        logger.info('run_hourly_checks: no eligible subscriptions')
        return {'status': 'ok', 'eligible': 0, 'emails_sent': 0}

    aggregated: dict[str, dict] = {
        'emails_sent': 0,
        'groups': 0,
        'owners_processed': 0,
        'eligible': len(eligible_ids),
    }

    by_owner: dict[int, list[int]] = defaultdict(list)
    for sub in Subscription.objects.filter(id__in=eligible_ids).only('id', 'owner_id'):
        by_owner[sub.owner_id].append(sub.pk)

    User = get_user_model()
    for owner_id, ids in by_owner.items():
        user = User.objects.get(pk=owner_id)
        qs = Subscription.objects.filter(id__in=ids)
        try:
            result = send_subscription_emails(user, qs)
        except Exception:
            logger.exception('send_subscription_emails failed for owner %s', owner_id)
            raise
        aggregated['emails_sent'] += result.get('emails_sent', 0)
        aggregated['groups'] += result.get('groups', 0)
        aggregated['owners_processed'] += 1

    logger.info('run_hourly_checks: %s', aggregated)
    return {'status': 'ok', **aggregated}


def send_now_group(owner_id: int, subscriber_email: str) -> dict:
    """
    Async task entry for Send Now.
    Send one merged email group for (owner_id, subscriber_email).
    """
    user = get_user_model().objects.get(pk=owner_id)
    merged_qs = Subscription.objects.filter(
        owner_id=owner_id,
        subscriber_email__iexact=subscriber_email,
    )
    return send_subscription_emails(user, merged_qs)
