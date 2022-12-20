import logging

from django.db import models
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
                model.add_to_class(
                    "lov_associated_entities",
                    models.ManyToManyField(
                        model.lov_entity_model,
                        through=model.lov_selections_model,
                        through_fields=("lov_value", "lov_entity"),
                        related_name=model.lov_associated_entities_related_name,
                        related_query_name=model.lov_associated_entities_related_query_name,
                    ),
                )

                model.objects._import_defaults()
        except Exception as e:
            logger.error(e)
