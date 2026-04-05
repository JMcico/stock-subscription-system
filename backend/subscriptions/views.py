import logging

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
