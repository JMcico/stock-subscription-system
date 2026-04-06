import logging
import os
import sys
import threading

from django.apps import AppConfig
from django.db.models.signals import post_migrate

logger = logging.getLogger(__name__)

SCHEDULE_NAME = 'run_hourly_subscription_checks'


def _ensure_q_schedule() -> None:
    from django.conf import settings
    from django.db.utils import OperationalError, ProgrammingError
    from django_q.models import Schedule

    q_name = (getattr(settings, 'Q_CLUSTER', {}) or {}).get('name') or None

    Schedule.objects.get_or_create(
        name=SCHEDULE_NAME,
        defaults={
            'func': 'subscriptions.tasks.run_hourly_checks',
            'schedule_type': Schedule.HOURLY,
            'repeats': -1,
            'cluster': q_name,
        },
    )


class SubscriptionsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'subscriptions'
    verbose_name = 'Subscriptions'

    def ready(self) -> None:
        # Import task module so Django-Q can resolve dotted paths
        from . import tasks  # noqa: F401

        if 'test' in sys.argv or os.environ.get('PYTEST_CURRENT_TEST'):
            return
        if os.environ.get('DJANGO_Q_SKIP_SCHEDULE'):
            return

        def _on_migrate(sender, app_config, **kwargs):
            if app_config.name != self.name:
                return
            try:
                _ensure_q_schedule()
            except Exception as e:
                logger.warning('Could not ensure Django-Q schedule after migrate: %s', e)

        post_migrate.connect(_on_migrate, dispatch_uid='subscriptions.ensure_q_schedule')

        def _defer_ensure() -> None:
            from django.db.utils import OperationalError, ProgrammingError

            try:
                _ensure_q_schedule()
            except (OperationalError, ProgrammingError) as e:
                logger.debug('Django-Q schedule deferred: %s', e)
            except Exception as e:
                logger.warning('Could not ensure Django-Q schedule: %s', e)

        threading.Thread(target=_defer_ensure, daemon=True).start()
