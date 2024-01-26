from django import forms

from flexible_list_of_values.forms import (
    LOVValueCreateFormMixin,
    LOVSelectionsModelForm,
)

from tests.testapp.models import TenantCropLOVSelection, TenantCropLOVValue, UserCrop


class TenantCropValueCreateForm(LOVValueCreateFormMixin, forms.ModelForm):
    """
    Form to let a tenant add a new custom LOV Value.
    """

    class Meta:
        model = TenantCropLOVValue
        fields = ["name", "lov_tenant", "value_type"]


class TenantCropValueSelectionForm(LOVSelectionsModelForm):
    """
    Form to let a tenant select which LOV Values its users can choose from.
    """

    class Meta:
        model = TenantCropLOVSelection

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["lov_selections"].widget.attrs["size"] = "10"


class UserCropSelectionForm(forms.ModelForm):
    """
    Form to let a Tenant's Users select from available LOV Values.
    """

    class Meta:
        model = UserCrop
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        # Get all allowed values for this tenant
        if self.instance:
            self.fields["crops"].queryset = TenantCropLOVSelection.objects.selected_values_for_tenant(
                self.instance.tenant
            )
            self.fields["user"].initial = self.user
            self.fields["tenant"].initial = self.instance.tenant
        else:
            self.fields["crops"].queryset = TenantCropLOVSelection.objects.none()

        self.fields["crops"].widget.attrs["size"] = "10"
