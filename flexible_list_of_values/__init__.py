from django.db import models
from django.utils.translation import gettext_lazy as _


class LOVValueType(models.TextChoices):
    """Allowable selections for List Of Values Value Types"""

    MANDATORY = "dm", _("Default Mandatory")  # Tenant can see, but not change this value
    OPTIONAL = "do", _("Default Optional")  # Tenant can see and select/unselect this value
    CUSTOM = "cu", _("Custom")  # Tenant created and can select/unselect this value
