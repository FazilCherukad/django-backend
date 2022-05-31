from django.apps import AppConfig
from core.utils import add_history_ip_address
from simple_history.tests.models import HistoricalPollWithExtraFields
from simple_history.signals import (
    pre_create_historical_record
)



class CoreConfig(AppConfig):
    name = 'core'

    def ready(self):
        pre_create_historical_record.connect(
            add_history_ip_address,
            sender=HistoricalPollWithExtraFields
        )
