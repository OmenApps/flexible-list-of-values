import logging

from django.apps import AppConfig

logger = logging.getLogger("flexible_list_of_values")


class FlexibleListOfValuesAppConfig(AppConfig):
    name = "flexible_list_of_values"
    verbose_name = "Flexible Lists of Values"

    def ready(self):
        pass
