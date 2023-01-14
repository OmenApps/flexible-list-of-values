from django.template.response import TemplateResponse

from tests.testapp.models import TenantCropLOVValue, UserCrop
from tests.testapp.forms import TenantCropValueCreateForm, TenantCropValueSelectionForm, UserCropSelectionForm


# Add decorator or other logic to allow only logged in users access to this view
def home_view(request):
    """
    Basic Home View
    """

    template = "testapp/home.html"
    context = {}

    return TemplateResponse(request, template, context)


# Add decorator or other logic to allow only logged in tenant owners access to this view
def lov_crop_value_create_view(request):
    """
    Form for creating new values for a Tenant
    """

    template = "testapp/create_value.html"
    context = {}

    # However you specify the current entity/tenant for the User submitting this form.
    # This is only an example.
    tenant = request.user.owned_tenants.first()

    # Here we provide the User's entity, which the form will use to determine the available Values
    form = TenantCropValueCreateForm(request.POST or None, lov_entity=tenant)

    if request.method == "POST":
        if form.is_valid():
            form.save()

    context["form"] = form

    # Provide the list of existing LOV Values for this Tenant
    context["existing_values"] = TenantCropLOVValue.objects.for_entity(tenant)

    return TemplateResponse(request, template, context)


# Add decorator or other logic to allow only logged in tenant owners access to this view
def lov_tenant_crop_selection_view(request):
    """
    Form for selecting the Values a tenant wants to use
    """

    template = "testapp/select_values.html"
    context = {}

    # However you specify the current entity/tenant for the User submitting this form.
    # This is only an example.
    tenant = request.user.owned_tenants.first()

    # Here we provide the entity
    form = TenantCropValueSelectionForm(request.POST or None, lov_entity=tenant)

    if request.method == "POST":
        if form.is_valid():
            form.save()
            # Update form's contents to ensure mandatory items are selected
            form = TenantCropValueSelectionForm(None, lov_entity=tenant)

    context["form"] = form

    return TemplateResponse(request, template, context)


# Add decorator or other logic to allow only logged in users who belong to a tenant to access to this view
def lov_user_crop_selection_view(request):
    """
    A for that allows a Tenant's Users to select the Crops they want to select
    """

    template = "testapp/select_values.html"
    context = {}

    # However you specify the current entity/tenant for the User submitting this form.
    # This is only an example.
    tenant = request.user.tenants.first()

    obj = obj, created = UserCrop.objects.get_or_create(
        user=request.user,
        tenant=tenant,
    )

    # Here we provide the entity
    form = UserCropSelectionForm(request.POST or None, instance=obj)
    if request.method == "POST":
        if form.is_valid():
            form.save()

    context["form"] = form
    return TemplateResponse(request, template, context)
