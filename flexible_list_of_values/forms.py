import logging

from django.forms import ModelForm

logger = logging.getLogger("flexible_list_of_values")

# See: https://bonidjukic.github.io/2019/01/18/dynamically-pass-model-to-django-modelform.html


def get_lov_values_model_form(concrete_model_class, form_fields="__all__"):
    """Provides a form to add new values"""

    class LOVValueModelForm(ModelForm):
        def __init__(self):
            # Check that we have a valid concrete_model
            super().__init__()

        class Meta:
            model = concrete_model_class
            fields = form_fields

    return LOVValueModelForm


def get_lov_selections_model_form(concrete_model_class, form_fields="__all__"):
    """Provides a form to allow an entity to select values"""

    class LOVSelectionsModelForm(ModelForm):
        def __init__(self):
            # Check that we have a valid concrete_model
            super().__init__()

        class Meta:
            model = concrete_model_class
            fields = form_fields

    return LOVSelectionsModelForm
