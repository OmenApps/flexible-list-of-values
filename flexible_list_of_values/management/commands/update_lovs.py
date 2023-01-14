import logging

from django.core.management.base import BaseCommand

logger = logging.getLogger("flexible_list_of_values")


class Command(BaseCommand):
    """Updates the project's Lists of Values"""

    help = "Updates the project's Lists of Values"

    def update_lovs(self):
        # Import default options for all concrete subclassed instances of AbstractLOVValue
        # from ...models import AbstractLOVValue
        from flexible_list_of_values.models import AbstractLOVValue

        try:
            for model in AbstractLOVValue.get_concrete_subclasses():
                model.objects._import_defaults()
        except Exception as e:
            logger.error(e)

    def handle(self, *args, **kwargs):
        self.update_lovs()
