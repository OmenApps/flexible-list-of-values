from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import gettext_lazy as _

from flexible_list_of_values import LOVValueType
from flexible_list_of_values.models import AbstractLOVSelection, AbstractLOVValue

User = get_user_model()


class Tenant(models.Model):
    """
    This model is a very simplistic example of how one might implement a Tenant architecture.
    """

    name = models.CharField(_("Tenant Name"), max_length=100)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="owned_tenants", null=True, blank=True)

    users = models.ManyToManyField(User, related_name="tenants", blank=True)

    def __str__(self):
        return self.name


class TenantCropLOVValue(AbstractLOVValue):
    """
    Concrete implementation of AbstractLOVValue with Crop options that a Tenant can modify.

    "Fruit", "Herbs and Spices", and "Vegetable" are mandatory selections, but the others are provided
        to the Tenants as optional recommendations. Tenants can also add their own custom Values.
    """

    lov_tenant_model = "testapp.Tenant"
    lov_selections_model = "testapp.TenantCropLOVSelection"

    lov_defaults = {
        "Fruit": {"value_type": LOVValueType.MANDATORY},  # 1
        "Fruit - Apple": {"value_type": LOVValueType.OPTIONAL},
        "Fruit - Berry": {"value_type": LOVValueType.OPTIONAL},
        "Fruit - Citrus": {"value_type": LOVValueType.OPTIONAL},
        "Fruit - Mellon": {"value_type": LOVValueType.OPTIONAL},
        "Fruit - Stone": {"value_type": LOVValueType.OPTIONAL},
        "Herbs and Spices": {"value_type": LOVValueType.MANDATORY},  # 2
        "Herbs and Spices - Basil": {"value_type": LOVValueType.OPTIONAL},
        "Herbs and Spices - Cilantro": {"value_type": LOVValueType.OPTIONAL},
        "Herbs and Spices - Rosemary": {"value_type": LOVValueType.OPTIONAL},
        "Herbs and Spices - Sage": {"value_type": LOVValueType.OPTIONAL},
        "Herbs and Spices - Thyme": {"value_type": LOVValueType.OPTIONAL},
        "Vegetable": {"value_type": LOVValueType.MANDATORY},  # 3
        "Vegetable - Avocado": {"value_type": LOVValueType.OPTIONAL},
        "Vegetable - Cabbage": {"value_type": LOVValueType.OPTIONAL},
        "Vegetable - Eggplant": {"value_type": LOVValueType.OPTIONAL},
        "Vegetable - Lettuce": {"value_type": LOVValueType.OPTIONAL},
        "Vegetable - Onion": {"value_type": LOVValueType.OPTIONAL},
        "Vegetable - Radish": {"value_type": LOVValueType.OPTIONAL},
        "Vegetable - Spinach": {"value_type": LOVValueType.OPTIONAL},
    }

    class Meta(AbstractLOVValue.Meta):
        verbose_name = "Tenant Crop Value"
        verbose_name_plural = "Tenant Crop Values"
        ordering = [
            "name",
        ]


class TenantCropLOVSelection(AbstractLOVSelection):
    """
    Concrete implementation of AbstractLOVSelection with actual selections
        of Crops that a Tenant's Users can select from in Forms
    """

    lov_value_model = "testapp.TenantCropLOVValue"
    lov_tenant_model = "testapp.Tenant"

    class Meta(AbstractLOVSelection.Meta):
        verbose_name = "Tenant Crop Selection"
        verbose_name_plural = "Tenant Crop Selections"

    def __str__(self):
        return self.lov_value.name


class UserCrop(models.Model):
    """
    The crops which a User belonging to a particular Tenant has selected.

    This is a very simplistic implementation of a Tenant-specific model and does not represent best practices.
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user_crops")
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="user_crops")

    crops = models.ManyToManyField(TenantCropLOVValue)
