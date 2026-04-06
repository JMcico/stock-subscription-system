"""
Merged subscription emails: group by subscriber_email, one OpenAI batch per group, one send per group.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from decimal import Decimal
from typing import TYPE_CHECKING

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone

from .models import NotificationLog, Subscription
from .utils import get_ai_recommendation, get_ai_recommendations_batch, get_price

if TYPE_CHECKING:
    from django.contrib.auth.models import User
    from django.db.models import QuerySet

logger = logging.getLogger(__name__)


def _signal_css_class(signal: str) -> str:
    s = (signal or 'Hold').strip().lower()
    if s == 'buy':
        return 'buy'
    if s == 'sell':
        return 'sell'
    return 'hold'


def _build_plain_text(rows: list[dict], subscriber_email: str, owner_label: str) -> str:
    lines = [
        'Stock subscription update',
        f'Recipient: {subscriber_email}',
        f'Account: {owner_label}',
        '',
    ]
    for r in rows:
        lines.append(
            f"- {r['ticker']}: ${r['price']} | Signal: {r['signal']} | {r['reason']}"
        )
    lines.extend(
        [
            '',
            'DISCLAIMER (not investment advice):',
            'Demo only. Not financial, legal, or tax advice.',
        ]
    )
    return '\n'.join(lines)


def send_subscription_emails(user: User, subscriptions: QuerySet | list[Subscription]) -> dict:
    """
    Group `subscriptions` by normalized subscriber_email; for each group fetch prices,
    one OpenAI batch call, send one HTML email, then update last_notified_* on each row.

    Prints merged HTML to stdout for local inspection (runserver console).
    """
    subs = list(subscriptions)
    if not subs:
        return {'emails_sent': 0, 'groups': 0, 'subscribers': []}

    groups: dict[str, list[Subscription]] = defaultdict(list)
    for s in subs:
        key = s.subscriber_email.strip().lower()
        groups[key].append(s)

    emails_sent = 0
    subscriber_emails: list[str] = []
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@example.com')

    for subscriber_email, rows in groups.items():
        ticker_price_pairs: list[tuple[str, Decimal]] = []
        for sub in rows:
            try:
                p = get_price(sub.ticker)
            except Exception as e:
                logger.warning('get_price failed for %s: %s', sub.ticker, e)
                p = Decimal('0')
            ticker_price_pairs.append((sub.ticker, p))

        # One OpenAI call per email group (batch); align recommendations to rows
        pair_strs = [(t, str(p)) for t, p in ticker_price_pairs]
        ai_list = get_ai_recommendations_batch(pair_strs)

        merged_rows: list[dict] = []
        for i, sub in enumerate(rows):
            price = ticker_price_pairs[i][1]
            ai = ai_list[i] if i < len(ai_list) else get_ai_recommendation(
                sub.ticker, price
            )
            sig = ai.get('signal', 'Hold')
            reason = ai.get('reason', '—')
            merged_rows.append(
                {
                    'ticker': sub.ticker,
                    'price': f'{price:.4f}',
                    'signal': sig,
                    'signal_class': _signal_css_class(sig),
                    'reason': reason,
                }
            )

        owner_label = user.get_username() or user.email or str(user.pk)
        context = {
            'subscriber_email': subscriber_email,
            'owner_label': owner_label,
            'rows': merged_rows,
        }
        html_body = render_to_string(
            'subscriptions/merged_subscription_email.html', context
        )
        text_body = _build_plain_text(merged_rows, subscriber_email, owner_label)

        subject = f'[Demo] Stock update: {", ".join(r["ticker"] for r in merged_rows)}'
        tickers_summary = ', '.join(r['ticker'] for r in merged_rows)

        print('\n' + '=' * 72)
        print('[send_subscription_emails] Merged email HTML (console preview)')
        print('=' * 72)
        print(html_body)
        print('=' * 72 + '\n')

        try:
            msg = EmailMultiAlternatives(
                subject=subject,
                body=text_body,
                from_email=from_email,
                to=[subscriber_email],
            )
            msg.attach_alternative(html_body, 'text/html')
            msg.send(fail_silently=False)
            emails_sent += 1
            subscriber_emails.append(subscriber_email)
            logger.info(
                'Merged email sent to %s (%d tickers)', subscriber_email, len(rows)
            )
            NotificationLog.objects.create(
                owner=user,
                tickers_summary=tickers_summary,
                recipient_email=subscriber_email,
                status=NotificationLog.Status.SUCCESS,
            )
        except Exception as e:
            logger.exception('Failed to send email to %s: %s', subscriber_email, e)
            NotificationLog.objects.create(
                owner=user,
                tickers_summary=tickers_summary,
                recipient_email=subscriber_email,
                status=NotificationLog.Status.FAILED,
            )
            raise

        now = timezone.now()
        for sub, (_, price) in zip(rows, ticker_price_pairs, strict=True):
            sub.last_notified_price = price
            sub.last_notified_time = now
            sub.save()

    return {
        'emails_sent': emails_sent,
        'groups': len(groups),
        'subscribers': subscriber_emails,
    }
