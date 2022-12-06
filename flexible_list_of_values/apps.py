import logging

from django.apps import AppConfig

logger = logging.getLogger("flexible_list_of_values")


class FlexibleListOfValuesAppConfig(AppConfig):
    name = "flexible_list_of_values"
    verbose_name = "Flexible Lists of Values"

    def ready(self):
        # Import default options for all concrete subclassed instances of AbstractLOVValue
        from .models import AbstractLOVValue

        try:
            for model in AbstractLOVValue.get_concrete_subclasses():
                model.objects._import_defaults()
        except Exception as e:
            logger.error(e)
