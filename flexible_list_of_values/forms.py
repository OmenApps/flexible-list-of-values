import logging

from django.forms import ModelForm

from .exceptions import NoEntityProvidedFromViewError


logger = logging.getLogger("flexible_list_of_values")

# See: https://bonidjukic.github.io/2019/01/18/dynamically-pass-model-to-django-modelform.html


class EntityValueCreateFormMixin:
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
        self.lov_entity = kwargs.pop("lov_entity", None)
        if not self.lov_entity:
            raise NoEntityProvidedFromViewError("No lov_entity model class was provided to the form from the view")
        super().__init__(*args, **kwargs)
        
        # Set the value_type field value to LOVValueType.CUSTOM and use a HiddenInput widget
        self.fields['value_type'].widget = HiddenInput()
        self.fields['value_type'].initial = LOVValueType.CUSTOM
        
        # Set the lov_entity field value to the entity instance provided from the view
        #   and use a HiddenInput widget
        self.fields['lov_entity'].widget = HiddenInput()
        self.fields['lov_entity'].initial = self.lov_entity

