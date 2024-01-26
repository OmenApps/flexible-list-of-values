import logging
from django.apps import apps
from django import forms
from django.forms.widgets import HiddenInput
from django.db import IntegrityError, transaction

from . import LOVValueType
from .exceptions import NoTenantProvidedFromViewError


logger = logging.getLogger("flexible_list_of_values")

# See: https://bonidjukic.github.io/2019/01/18/dynamically-pass-model-to-django-modelform.html


class LOVFormBaseMixin:
    """Checks that we have a valid lov_tenant value passed in from the view."""

    def __init__(self, *args, **kwargs):
        self.lov_tenant = kwargs.pop("lov_tenant", None)
        if not self.lov_tenant:
            raise NoTenantProvidedFromViewError(
                "No lov_tenant model class was provided to the form from the view. "
                "Ensure that 'lov_tenant' is passed as an argument."
            )
        super().__init__(*args, **kwargs)


class LOVValueCreateFormMixin(LOVFormBaseMixin):
    """Used in forms that allow an tenant to create a new custom value.

    It requires an `lov_tenant` argument to be passed from the view. This should be an instance of the model
      class provided in the lov_tenant_model parameter of the concrete LOVValueModel.

    Usage:

        class MyValueCreateForm(TenantValueCreateFormMixin, forms.ModelForm):
            class Meta:
                model = MyConcreteLOVValueModel


        def my_values_view(request):
            form = MyValueCreateForm(request.POST, lov_tenant=request.user.tenant)
    """
    
    def get_value_type_widget(self):
        """Returns the widget to use for the value_type field."""
        return HiddenInput()
    
    def get_lov_tenant_widget(self):
        """Returns the widget to use for the lov_tenant field."""
        return HiddenInput()

    def __init__(self, *args, **kwargs):
        """Sets the value_type and lov_tenant fields to the correct values."""
        super().__init__(*args, **kwargs)

        # Set the value_type field value to LOVValueType.CUSTOM and use a HiddenInput widget
        self.fields["value_type"].widget = self.get_value_type_widget()
        self.fields["value_type"].initial = LOVValueType.CUSTOM

        # Set the lov_tenant field value to the tenant instance provided from the view
        #   and use a HiddenInput widget
        self.fields["lov_tenant"].widget = self.get_lov_tenant_widget()
        self.fields["lov_tenant"].initial = self.lov_tenant

    def clean(self):
        """Ensures that the value_type and lov_tenant fields are correct even if the HiddenInput widget was manipulated."""
        cleaned_data = super().clean()

        # ensure value_type and lov_tenant is correct even if HiddenField was manipulated
        cleaned_data["value_type"] = LOVValueType.CUSTOM
        cleaned_data["lov_tenant"] = self.lov_tenant
        return cleaned_data


class LOVModelMultipleChoiceField(forms.ModelMultipleChoiceField):
    """Displays objects and shows which are mandatory."""

    def label_from_instance(self, obj):
        """Displays objects and shows which are mandatory.
        
        Override this method to change the display of the objects in the field.
        """
        if obj.value_type == LOVValueType.MANDATORY:
            return f"{obj.name} (mandatory)"
        return obj.name


class LOVSelectionsModelForm(LOVFormBaseMixin, forms.Form):
    """
    Creates a form with a `lov_selections` field, using LOVModelMultipleChoiceField

    Usage:
        class MyModelForm(LOVSelectionsModelForm):
            class Meta:
                model = TenantCropLOVSelection
    """

    lov_selections = LOVModelMultipleChoiceField(queryset=None)

    def __init__(self, *args, **kwargs):
        self._meta = self.Meta
        self.lov_selection_model = self._meta.model
        self.lov_value_model = apps.get_model(self.lov_selection_model.lov_value_model)
        super().__init__(*args, **kwargs)

        # Get all allowed values for this tenant
        self.fields["lov_selections"].queryset = self.lov_selection_model.objects.values_for_tenant(self.lov_tenant)

        # Make sure the current selections (and mandatory values) are selected in the form
        self.fields["lov_selections"].initial = self.lov_selection_model.objects.selected_values_for_tenant(
            self.lov_tenant
        )

        self.fields["lov_selections"].widget.attrs["size"] = "10"

    def clean(self):
        """Ensures that the lov_selections field is correct even if the HiddenInput widget was manipulated."""
        cleaned_data = super().clean()

        # ensure lov_selections contain mandatory items even if HiddenField was manipulated
        cleaned_lov_selections = (
            cleaned_data["lov_selections"] | self.lov_value_model.objects.filter(value_type=LOVValueType.MANDATORY)
        ).distinct()

        self.removed_selections = self.lov_value_model.objects.exclude(id__in=cleaned_lov_selections)

        cleaned_data["lov_selections"] = cleaned_lov_selections

        return cleaned_data

    def save(self, *args, **kwargs):
        try:
            with transaction.atomic():
                for selection in self.cleaned_data["lov_selections"]:
                    self.lov_selection_model.objects.update_or_create(lov_tenant=self.lov_tenant, lov_value=selection)
                self.lov_selection_model.objects.filter(lov_value__in=self.removed_selections).delete()
        except IntegrityError as e:
            logger.warning(f"Problem creating or deleting selections for {self.lov_tenant}: {e}")
        super().save(*args, **kwargs)
