from django.db import models
from django.utils.translation import gettext_lazy as _


class LOVValueType(models.TextChoices):
    """Allowable selections for List Of Values Value Types"""

    MANDATORY = "dm", _("Default Mandatory")  # Entity can see, but not change this value
    OPTIONAL = "do", _("Default Optional")  # Entity can see and select/unselect this value
    CUSTOM = "cu", _("Custom")  # Entity created and can select/unselect this value
