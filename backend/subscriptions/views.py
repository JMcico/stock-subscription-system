import logging

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from .models import Subscription
from .permissions import IsSubscriptionOwnerOrStaff
from .serializers import SubscriptionSerializer
from .services import send_subscription_emails
from .utils import get_price, validate_ticker_exists

logger = logging.getLogger(__name__)


class SubscriptionViewSet(ModelViewSet):
    """
    Regular users: own subscriptions only. Staff: all rows.
    """

    serializer_class = SubscriptionSerializer
    permission_classes = [IsAuthenticated, IsSubscriptionOwnerOrStaff]

    def get_queryset(self):
        user = self.request.user
        qs = Subscription.objects.select_related('owner')
        if user.is_staff:
            return qs.all()
        return qs.filter(owner=user)

    @action(detail=False, methods=['post'], url_path='send_now')
    def send_now_bulk(self, request):
        """
        One-click send from dashboard: for current scoped queryset, merge by
        (owner, subscriber_email) and send one email per group.
        """
        scoped = self.get_queryset()
        groups = (
            scoped.values_list('owner_id', 'subscriber_email')
            .distinct()
        )
        if not groups:
            return Response(
                {'status': 'sent', 'emails_sent': 0, 'groups': 0, 'subscribers': []},
                status=status.HTTP_200_OK,
            )

        aggregated = {'emails_sent': 0, 'groups': 0, 'subscribers': []}
        for owner_id, subscriber_email in groups:
            owner = scoped.model._meta.get_field('owner').related_model.objects.get(
                pk=owner_id
            )
            merged_qs = Subscription.objects.filter(
                owner=owner,
                subscriber_email__iexact=subscriber_email,
            )
            try:
                result = send_subscription_emails(owner, merged_qs)
            except Exception as e:
                logger.exception('send_now bulk failed: %s', e)
                return Response(
                    {'detail': str(e), 'code': 'send_failed'},
                    status=status.HTTP_502_BAD_GATEWAY,
                )
            aggregated['emails_sent'] += result.get('emails_sent', 0)
            aggregated['groups'] += result.get('groups', 0)
            aggregated['subscribers'].extend(result.get('subscribers', []))

        return Response(
            {
                'status': 'sent',
                'emails_sent': aggregated['emails_sent'],
                'groups': aggregated['groups'],
                'subscribers': sorted(set(aggregated['subscribers'])),
            },
            status=status.HTTP_200_OK,
        )

    @action(
        detail=False,
        methods=['post'],
        url_path=r'owners/(?P<owner_id>[^/.]+)/send_now',
    )
    def send_now_owner(self, request, owner_id=None):
        """
        Admin owner-level one-click send: send for one owner only, merged by
        subscriber_email within that owner.
        """
        try:
            owner_id_int = int(owner_id)
        except (TypeError, ValueError):
            return Response(
                {'detail': 'Invalid owner id.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = request.user
        if not user.is_staff and owner_id_int != user.pk:
            return Response({'detail': 'Forbidden.'}, status=status.HTTP_403_FORBIDDEN)

        owner = get_user_model().objects.filter(pk=owner_id_int).first()
        if owner is None:
            return Response({'detail': 'Owner not found.'}, status=status.HTTP_404_NOT_FOUND)

        groups = (
            Subscription.objects.filter(owner=owner)
            .values_list('subscriber_email', flat=True)
            .distinct()
        )
        if not groups:
            return Response(
                {'status': 'sent', 'emails_sent': 0, 'groups': 0, 'subscribers': []},
                status=status.HTTP_200_OK,
            )

        aggregated = {'emails_sent': 0, 'groups': 0, 'subscribers': []}
        for subscriber_email in groups:
            merged_qs = Subscription.objects.filter(
                owner=owner,
                subscriber_email__iexact=subscriber_email,
            )
            try:
                result = send_subscription_emails(owner, merged_qs)
            except Exception as e:
                logger.exception('send_now owner failed: %s', e)
                return Response(
                    {'detail': str(e), 'code': 'send_failed'},
                    status=status.HTTP_502_BAD_GATEWAY,
                )
            aggregated['emails_sent'] += result.get('emails_sent', 0)
            aggregated['groups'] += result.get('groups', 0)
            aggregated['subscribers'].extend(result.get('subscribers', []))

        return Response(
            {
                'status': 'sent',
                'emails_sent': aggregated['emails_sent'],
                'groups': aggregated['groups'],
                'subscribers': sorted(set(aggregated['subscribers'])),
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=['post'], url_path='send_now')
    def send_now(self, request, pk=None):
        """
        Merge all subscriptions for the **same owner** and **same subscriber_email** as this row,
        send one email per distinct subscriber_email (spec.md §6), then update last_notified_*.
        """
        subscription = self.get_object()
        owner = subscription.owner
        merged_qs = Subscription.objects.filter(
            owner=owner,
            subscriber_email__iexact=subscription.subscriber_email,
        )
        try:
            result = send_subscription_emails(owner, merged_qs)
        except Exception as e:
            logger.exception('send_now failed: %s', e)
            return Response(
                {'detail': str(e), 'code': 'send_failed'},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        return Response(
            {
                'status': 'sent',
                'emails_sent': result['emails_sent'],
                'groups': result['groups'],
                'subscribers': result['subscribers'],
            },
            status=status.HTTP_200_OK,
        )


class ValidateTickerView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        raw = request.data.get('ticker', '')
        try:
            symbol = validate_ticker_exists(raw)
            price = get_price(symbol)
        except ValueError as e:
            return Response(
                {'valid': False, 'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            return Response(
                {'valid': False, 'error': str(e)},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        return Response(
            {
                'valid': True,
                'ticker': symbol,
                'price': str(price),
            },
            status=status.HTTP_200_OK,
        )
