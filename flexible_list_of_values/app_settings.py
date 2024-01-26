from django.conf import settings
from django.db.models.base import ModelBase


# There is likely no reason ever to change the model base, but it is provided as an setting
# here for completeness.
LOV_MODEL_BASE = getattr(settings, 'LOV_MODEL_BASE', ModelBase)

