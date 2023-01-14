import logging
from django.apps import apps
from django import forms
from django.forms.widgets import HiddenInput
from django.db import IntegrityError, transaction

from . import LOVValueType
from .exceptions import NoEntityProvidedFromViewError


logger = logging.getLogger("flexible_list_of_values")

# See: https://bonidjukic.github.io/2019/01/18/dynamically-pass-model-to-django-modelform.html


class LOVFormBaseMixin:
    """
    Checks that we have a valid lov_entity value passed in from the view
    """

    def __init__(self, *args, **kwargs):
        self.lov_entity = kwargs.pop("lov_entity", None)
        if not self.lov_entity:
            raise NoEntityProvidedFromViewError("No lov_entity model class was provided to the form from the view")
        super().__init__(*args, **kwargs)


class LOVValueCreateFormMixin(LOVFormBaseMixin):
    """
    Used in forms that allow an entity to create a new custom value.

    It requires an `lov_entity` argument to be passed from the view. This should be an instance of the model
      class provided in the lov_entity_model parameter of the concrete LOVValueModel.

    Usage:

        class MyValueCreateForm(EntityValueCreateFormMixin, forms.ModelForm):
            class Meta:
                model = MyConcreteLOVValueModel


        def my_values_view(request):
            form = MyValueCreateForm(request.POST, lov_entity=request.user.tenant)
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Set the value_type field value to LOVValueType.CUSTOM and use a HiddenInput widget
        self.fields["value_type"].widget = HiddenInput()
        self.fields["value_type"].initial = LOVValueType.CUSTOM

        # Set the lov_entity field value to the entity instance provided from the view
        #   and use a HiddenInput widget
        self.fields["lov_entity"].widget = HiddenInput()
        self.fields["lov_entity"].initial = self.lov_entity

    def clean(self):
        cleaned_data = super().clean()

        # # if this Item already exists
        # if self.instance:
        #     # ensure value_type and lov_entity is correct even if HiddenField was manipulated
        #     cleaned_data["value_type"] = LOVValueType.CUSTOM
        #     cleaned_data["lov_entity"] = self.lov_entity

        # ensure value_type and lov_entity is correct even if HiddenField was manipulated
        cleaned_data["value_type"] = LOVValueType.CUSTOM
        cleaned_data["lov_entity"] = self.lov_entity
        return cleaned_data


class LOVModelMultipleChoiceField(forms.ModelMultipleChoiceField):
    """
    Displays objects and shows which are mandatory
    """

    def label_from_instance(self, obj):
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
        self.fields["lov_selections"].queryset = self.lov_selection_model.objects.values_for_entity(self.lov_entity)

        # Make sure the current selections (and mandatory values) are selected in the form
        self.fields["lov_selections"].initial = self.lov_selection_model.objects.selected_values_for_entity(
            self.lov_entity
        )

        self.fields["lov_selections"].widget.attrs["size"] = "10"

    def clean(self):
        cleaned_data = super().clean()

        # ensure value_type and lov_selections contain mandatory items even if HiddenField was manipulated
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
                    self.lov_selection_model.objects.update_or_create(lov_entity=self.lov_entity, lov_value=selection)
                self.lov_selection_model.objects.filter(lov_value__in=self.removed_selections).delete()
        except IntegrityError as e:
            logger.warning(f"Problem creating or deleting selections for {self.lov_entity}: {e}")
        super().__init__(*args, **kwargs, lov_entity=self.lov_entity)
