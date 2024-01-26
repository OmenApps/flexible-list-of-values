# flexible-list-of-values

Flexible and Extensible Lists of Values (LOV) for Django

*flexible-list-of-values* provides you a way to give your SaaS app's tenants customization options in its User-facing forms, but also lets you provide them with defaults - either mandatory or optional - to prevent each tenant having to "recreate the wheel".

> When adding customizability to a SaaS app, there are a variety of approaches and tools:
> 
> - [Dynamic models](https://baserow.io/blog/how-baserow-lets-users-generate-django-models) and dynamic model fields
> - [Entity-Attribute-Value (EAV)](https://en.wikipedia.org/wiki/Entity%E2%80%93attribute%E2%80%93value_model)
> - Adding [JSONField](https://docs.djangoproject.com/en/4.1/ref/models/fields/#jsonfield) to a model
>
> But these approaches can be a bit *too* flexible. Sometimes we want to provide guardrails for our tenants.

*Note: The term "tenant" in this package to refers to a model within your project that has associated Users, and which has "ownership" over the LOV value options provided to its end-users/customers*

## Contents

- [flexible-list-of-values](#flexible-list-of-values)
  - [Contents](#contents)
  - [Potential Use-Cases](#potential-use-cases)
  - [Example implementation](#example-implementation)
    - [The Testapp Project](#the-testapp-project)
      - [Setup with Docker Compose](#setup-with-docker-compose)
      - [Working with the Testapp Project](#working-with-the-testapp-project)
      - [Working with LOV Values in the Testapp Project](#working-with-lov-values-in-the-testapp-project)
      - [Letting tenants select LOV value choices for their users](#letting-tenants-select-lov-value-choices-for-their-users)
      - [Working with a tenant's LOV Selections](#working-with-a-tenants-lov-selections)
  - [API](#api)
    - [Model: AbstractLOVValue](#model-abstractlovvalue)
      - [Fields](#fields)
      - [Model attributes](#model-attributes)
      - [Model Hooks](#model-hooks)
      - [Manager and QuerySet Methods](#manager-and-queryset-methods)
      - [Manager Hooks](#manager-hooks)
    - [Model: AbstractLOVSelection](#model-abstractlovselection)
      - [Fields](#fields-1)
      - [Model attributes](#model-attributes-1)
      - [Model Hooks](#model-hooks-1)
      - [Manager and QuerySet Methods](#manager-and-queryset-methods-1)
  - [Management Commands](#management-commands)
  - [Settings](#settings)


## Potential Use-Cases

The `flexible-list-of-values` package is a versatile tool for Django applications, offering dynamic and customizable management of lists of values (LOVs). This package is especially beneficial in scenarios where different users or groups within an application (referred to as tenants) require the ability to define and select from a set of predefined options that are then provided to their customers or end users in forms. Here are some use-cases:

In a **Django-based project management application** for engineering firms:

- **Tenant Structure**: Each engineering firm acts as a tenant, and its employees are the end-users.
- **Mandatory Task Statuses**: The application developer can set mandatory task status options (like "Assigned", "Started") that are always included in task-related forms for all employees of every tenant.
- **Optional Task Statuses**: The developer can also provide a list of optional task statuses (like "Awaiting Review", "On Hold") that each firm (tenant) can choose to include in these forms.
- **Custom Task Statuses**: Additionally, each firm can define its own set of task statuses (like "In Progress", "Review", "Done") tailored to their specific workflow needs.


In a scenario where an **HR management system** is used within a company:

- **Tenant Structure**: The HR department is the tenant, and the various departments within the company are the end-users.
- **Mandatory Job Titles**: The application developer can specify mandatory job titles (like "Manager", "Team Lead") that each HR department must include in forms for departmental use.
- **Optional Job Titles**: The developer can also provide a list of optional job titles (like "Senior Analyst", "Project Coordinator") that the HR department can choose to include in the forms.
- **Custom Job Titles**: Each HR department has the flexibility to create their own custom job title options (like "Innovation Specialist", "Digital Strategist") to cater to the unique roles within their company.

For **Marketplace Platforms**:

- **Tenant Structure**: The vendor is the tenant, and visitors to the vendor's store are the end-users.
- **Dynamic Filtering Options**: As above, the application developer can provide mandatory/optional options that the vendor must/can use in forms that filter product searches based on these customizable attributes. And the vendor can supply their own custom search options as well.

In **Learning Management Systems (LMS)**:

- **Tenant Structure**: The school is the tenant, and instructors are are the users.
- **Course and Program Management**: The application developer can provide mandatory/optional options that schools must/can offer to instructors for use in forms that customize course types, credit values, or grading schemes when creating their courses. Each school can also provide it's own custom course types, credit values, or grading schemes options that instructor can choose from.

In applications for **managing building permits** in a municipality:

- **Tenant Structure**: Each municipality is a tenant, and businesses & homeowners requesting building permits are the end-users.
- **Permit Request Forms**: Municipalities can customize form options for it's users, creating it's own custom "property type" options that the users can select from. Municipalities can also choose any of the developer-provided optional "property type" options for the form field. And any developer-provided mandatory "property type" options will always be available for users to select.

## Example implementation

Imagine your project provides a form that allows your tenants' users provide details about their garden plots. Now you want to add a "crops" field to this form so that each tenants' users can also record the specific crops they are growing.

You could hard-code some crop value choices using CharField and choices, or if your tenants wanted the field to be customizable you could use JSONField or other methods, but this can get sloppy.

`flexible-list-of-values` provides an in-between option. You can specify some default options that are mandatory for all users, regardless of tenant, provide some default options that your tenants can either use or discard, and allow additional custom value options specific to the tenant and its users.

![Descriptive Diagram](https://raw.githubusercontent.com/jacklinke/flexible-list-of-values/main/docs/media/FlexibleLOVDescription.png)


### The Testapp Project

To help explain the package, we provide a demonstration project. Below, we describe how to set up the project using Docker Compose,
 and how to work with the LOV Values and Selections.

#### Setup with Docker Compose

To help you quickly test and understand the flexible-list-of-values package, we provide a Docker Compose setup with a demonstration project. In order to utilize the project, we assume here that you have downloaded or cloned a copy of the [project code repository](https://github.com/jacklinke/flexible-list-of-values), and that you already have docker compose installed. If not, see [the compose docs](https://docs.docker.com/compose/install/).

Navigate to the "flexible-list-of-values" directory, and create a virtual environment to work from:

`python3 -m venv .venv`
    
Then activate the environment:

`source .venv/bin/activate`

Build the project:

`docker compose build`

Then run migrations and create a superuser.

```bash
python manage.py migrate
python manage.py createsuperuser
```

To synchronize the "lov_default" values with the database, run

`python manage.py update_lovs`

Bring the docker compose project up, where it will be available at http://127.0.0.1:8000/

`docker compose up -d`

Optionally create another user or two in [admin](http://127.0.0.1:8000/admin/)

Within admin, create at least one tenant, setting the owner and users fields. The tenant owner can create new LOV Values and choose which Values its Users can select from.

If the user account you are logged in with is a tenant owner, then [click here](http://127.0.0.1:8000/lov_crop_value_create_view/) to add new LOV Values, or [click here](http://127.0.0.1:8000/lov_tenant_crop_selection_view/) to specify which Values your users can choose from. 

If the user account you are logged in with belongs to a tenant, then [click here](http://127.0.0.1:8000/lov_user_crop_selection_view/) to choose from among the LOV Value choices the tenant has made available to you.

*See the Test Project in the [project repo](https://github.com/jacklinke/flexible-list-of-values) for full details.*

#### Working with the Testapp Project

Here is what is going on behind the scenes.

models.py:

```python
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

    "Fruit", "Herbs and Spices", and "Vegetable" are mandatory selections, but the others are provided to the Tenants as optional recommendations. Tenants can also add their own custom Values.
    """
    lov_tenant_model = "testapp.Tenant"
    lov_selections_model = "testapp.TenantCropLOVSelection"

    lov_defaults = {
        "Fruit": {"value_type": LOVValueType.MANDATORY},  # 1
        "Fruit - Apple": {"value_type": LOVValueType.OPTIONAL},
        "Fruit - Mellon": {"value_type": LOVValueType.OPTIONAL},
        "Fruit - Stone": {"value_type": LOVValueType.OPTIONAL},
        "Herbs and Spices": {"value_type": LOVValueType.MANDATORY},  # 2
        "Herbs and Spices - Basil": {"value_type": LOVValueType.OPTIONAL},
        "Herbs and Spices - Sage": {"value_type": LOVValueType.OPTIONAL},
        "Herbs and Spices - Thyme": {"value_type": LOVValueType.OPTIONAL},
        "Vegetable": {"value_type": LOVValueType.MANDATORY},  # 3
        "Vegetable - Avocado": {"value_type": LOVValueType.OPTIONAL},
        "Vegetable - Cabbage": {"value_type": LOVValueType.OPTIONAL},
        "Vegetable - Spinach": {"value_type": LOVValueType.OPTIONAL},
    }

    class Meta(AbstractLOVValue.Meta):
        verbose_name = "Tenant Crop Value"
        verbose_name_plural = "Tenant Crop Values"
        ordering = ["name"]


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
    The crops which a User belonging to a particular Tenant has selected for their garden plot. (This is a very simplistic implementation of a Tenant-specific model and does not represent best practices.)
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user_crops")
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="user_crops")

    crops = models.ManyToManyField(TenantCropLOVValue)
```

For the example above, in a UserCrop form for Users of TenantA or TenantB ...

- The `crops` ModelChoiceField will always include Crop choices for "Fruit", "Herbs and Spices", and "Vegetable".
- Both tenants can choose whether their Users will have the other values listed in `lov_defaults`.
- And both tenants can create custom tenant-specific value options for their Users to choose from.

#### Working with LOV Values in the Testapp Project

View the available Values for a Tenant:

```python
tenant = Tenant.objects.first()
values_for_tenant = TenantCropLOVValue.objects.for_tenant(tenant)
```

Alternately:

```python
tenant = Tenant.objects.first()
values_for_tenant = TenantCropLOVSelection.objects.values_for_tenant(tenant)
```

View the selected Values for this Tenant:

```python
tenant = Tenant.objects.first()
selected_values_for_tenant = TenantCropLOVSelection.objects.selected_values_for_tenant(tenant)
```

Create new custom Values for this Tenant:

```python
tenant = Tenant.objects.first()
TenantCropLOVValue.objects.create_for_tenant(tenant, "New Value for this Tenant")
```

Delete Values for this Tenant (only deletes custom values owned by this tenant)

```python
tenant = Tenant.objects.first()
values = TenantCropLOVValue.objects.for_tenant(tenant=tenant).filter(name__icontains="Something")
for value in values:
    value.delete()
```

#### Letting tenants select LOV value choices for their users

Tenants can select from among the Values available for this Tenant or create new Values

forms.py:

```python
from django import forms
from flexible_list_of_values.forms import (
    LOVValueCreateFormMixin,
    LOVSelectionsModelForm,
)
from tests.testapp.models import TenantCropLOVSelection, TenantCropLOVValue


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
```

views.py

```python
from django.template.response import TemplateResponse
from tests.testapp.models import TenantCropLOVValue
from tests.testapp.forms import TenantCropValueCreateForm, TenantCropValueSelectionForm


# Add decorator or other logic to allow only logged in tenant owners access to this view
def lov_crop_value_create_view(request):
    """
    Form for creating new values for a Tenant
    """

    template = "testapp/create_value.html"
    context = {}

    # However you specify the current tenant for the User submitting this form.
    # This is only an example.
    tenant = request.user.owned_tenants.first()

    # Here we provide the User's associated tenant, which the form will use to determine the available Values
    form = TenantCropValueCreateForm(request.POST or None, lov_tenant=tenant)

    if request.method == "POST":
        if form.is_valid():
            form.save()

    context["form"] = form

    # Provide the list of existing LOV Values for this Tenant
    context["existing_values"] = TenantCropLOVValue.objects.for_tenant(tenant)

    return TemplateResponse(request, template, context)


# Add decorator or other logic to allow only logged in tenant owners access to this view
def lov_tenant_crop_selection_view(request):
    """
    Form for selecting the Values a tenant wants to use
    """

    template = "testapp/select_values.html"
    context = {}

    # However you specify the current tenant associated with the User submitting this form.
    # This is only an example.
    tenant = request.user.owned_tenants.first()

    # Here we provide the tenant
    form = TenantCropValueSelectionForm(request.POST or None, lov_tenant=tenant)

    if request.method == "POST":
        if form.is_valid():
            form.save()
            # Update form's contents to ensure mandatory items are selected
            form = TenantCropValueSelectionForm(None, lov_tenant=tenant)

    context["form"] = form

    return TemplateResponse(request, template, context)
```

#### Working with a tenant's LOV Selections

A Tenant's Users make a choice from among the selected Values for this Tenant each time they fill out a UserCrop Selection Form.

forms.py (continued from previous forms.py code):

```python
from django import forms
from tests.testapp.models import UserCrop

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
            self.fields["crops"].queryset = TenantCropLOVSelection.objects.selections_for_tenant(self.instance.tenant)
            self.fields["user"].initial = self.user
            self.fields["tenant"].initial = self.instance.tenant
        else:
            self.fields["crops"].queryset = TenantCropLOVSelection.objects.none()

        self.fields["crops"].widget.attrs["size"] = "10"
```

views.py (continued from previous views.py code):

```python
from django.template.response import TemplateResponse
from tests.testapp.models import UserCrop
from tests.testapp.forms import UserCropSelectionForm

# Add decorator or other logic to allow only logged in users who belong to a tenant to access to this view
def lov_user_crop_selection_view(request):
    """
    A for that allows a Tenant's Users to select the Crops they want to select
    """

    template = "testapp/select_values.html"
    context = {}

    # However you specify the current tenant associated with the User submitting this form.
    # This is only an example.
    tenant = request.user.tenants.first()

    obj = obj, created = UserCrop.objects.get_or_create(
        user=request.user,
        tenant=tenant,
    )

    # Here we provide the tenant
    form = UserCropSelectionForm(request.POST or None, instance=obj)
    if request.method == "POST":
        if form.is_valid():
            form.save()

    context["form"] = form
    return TemplateResponse(request, template, context)
```

Here, Users for TenantA who are filling out a UserCropSelectionForm form will see all mandatory values, the optional values that TenantA has selected, and any custom values TenantA has created. TenantB's users will see all mandatory values, the optional values that TenantB has selected, and any custom values TenantB has created.


## API

### Model: AbstractLOVValue

#### Fields

- **id**: default id
- **name** (CharField): The name or title of the value to be used.
- **lov_tenant** (FK): the owning tenant for this value. If this is a default value, this field will be null.
- **lov_associated_tenants** (M2M): all tenants this value is associated with. (The reverse relationship on the tenant model is all values selected for the tenant)
- **value_type** (CharField): Any of
    - LOVValueType.MANDATORY
    - LOVValueType.OPTIONAL
    - LOVValueType.CUSTOM
- **deleted** (DateTimeField): The datetime this value was deleted, or null if it is not deleted.


#### Model attributes


- **`lov_defaults`**  
  A dictionary of default mandatory and optional values from which an tenant can select. See usage examples above.
  *Default*: `{}`

- **`lov_tenant_model`**  
  Specifies the model class for the 'tenant' in your project which can customize its Users' LOVs. Specify the string representation of the model class (e.g.: `"tenants.Tenant"`).
  *Required*

- **`lov_tenant_on_delete`**  
  What should happen when the related tenant instance is deleted.
  *Default*: `models.CASCADE`

- **`lov_tenant_model_related_name`**  
  `related_name` for the related tenant instance.
  *Default*: `"%(app_label)s_%(class)s_related"`

- **`lov_tenant_model_related_query_name`**  
  `related_query_name` for the related tenant instance.
  *Default*: `"%(app_label)s_%(class)ss"`

- **`lov_selections_model`**  
  Specifies the model class of the through-model between an Tenant and a Value. Each instance of this through-model is an option that the tenant's users can choose from. Must be a concrete subclass of AbstractLOVSelection. Specify the string representation of the model class (e.g.: `"tenants.TenantCropLOVSelection"`).
  *Required*

- **`lov_associated_tenants_related_name`**  
  `related_name` for the M2M to the tenant instance.
  *Default*: `"%(app_label)s_%(class)s_related"`

- **`lov_associated_tenants_related_query_name`**  
  `related_query_name` for the M2M to the tenant instance.
  *Default*: `"%(app_label)s_%(class)ss"`

#### Model Hooks

The `AbstractLOVValue` model provides several hooks for extending or customizing its behavior. These hooks allow developers to add custom logic before and after saving an instance and to implement additional validation logic.

- **`before_save(*args, **kwargs)`**  
  Called before an instance of `AbstractLOVValue` is saved. Override this method to add custom pre-save behavior.

  ```python
  def before_save(self, *args, **kwargs):
      # Custom pre-save logic here
  ```

- **`after_save(*args, **kwargs)`**  
  Called after an instance of `AbstractLOVValue` is saved. Override this method to add custom post-save behavior.

  ```python
  def after_save(self, *args, **kwargs):
      # Custom post-save logic here
  ```

#### Manager and QuerySet Methods

- **`for_tenant(tenant)`**  
  Returns QuerySet of all available values for a given tenant, including:
  - all required default values
  - all non-required default values
  - all tenant-specific values for this tenant

- **`create_for_tenant(tenant, name: str)`**  
  Creates a new selectable Value for the provided tenant.

- **`create_mandatory(name: str)`**  
  Creates a new Value (selected for all tenants).

- **`create_optional(name: str)`**  
  Creates a new selectable optional Value (selectable by all tenants).

#### Manager Hooks

The `LOVValueManager` provides hooks for customizing the behavior of creating new instances. These hooks are useful for adding custom logic before and after creating a new `LOVValue`.

- **`before_create(*args, **kwargs)`**  
  Called before a new instance of `LOVValue` is created. Override this method to add custom pre-create behavior.

  ```python
  def before_create(self, *args, **kwargs):
      # Custom pre-create logic here
  ```

- **`after_create(obj, *args, **kwargs)`**  
  Called after a new instance of `LOVValue` is created. Override this method to add custom post-create behavior.

  ```python
  def after_create(self, obj, *args, **kwargs):
      # Custom post-create logic here
  ```

### Model: AbstractLOVSelection

This is a through-model from an concrete LOVValue model instance to a tenant model instance representing the value selections a tenant has made.

#### Fields

- **id**: default id
- **lov_tenant** (FK): the tenant this selection is associated with.
- **lov_value** (FK): the value this selection is associated with.

#### Model attributes

- **`lov_tenant_model`**  
  Specifies the model class for the 'tenant' in your project which can customize its Users' LOVs. Specify the string representation of the model class (e.g.: `"tenants.Tenant"`).
  *Required*

- **`lov_tenant_on_delete`**  
  What should happen when the related tenant instance is deleted.
  *Default*: `models.CASCADE`

- **`lov_tenant_model_related_name`**  
  `related_name` for the related tenant instance.
  *Default*: `"%(app_label)s_%(class)s_related"`

- **`lov_tenant_model_related_query_name`**  
  `related_query_name` for the related tenant instance.
  *Default*: `"%(app_label)s_%(class)ss"`

- **`lov_value_model`**  
  Specifies the model class for the concrete (not abstract!) subclass of AbstractLOVValue. Specify the string representation of the model class (e.g.: `"contacts.TenantCropLOVSelection"`).
  *Required*

- **`lov_value_model_related_name`**  
  `related_name` for the related concrete subclassed AbstractLOVValue instance.
  *Default*: `"%(app_label)s_%(class)s_related"`

- **`lov_value_model_related_query_name`**  
  `related_query_name` for the related concrete subclassed AbstractLOVValue instance.
  *Default*: `"%(app_label)s_%(class)ss"`

#### Model Hooks

The `AbstractLOVSelection` model provides several hooks for extending or customizing its behavior. These hooks allow developers to add custom logic before and after saving an instance and to implement additional validation logic.

- **`before_save(*args, **kwargs)`**  
  Called before an instance of `AbstractLOVValue` is saved. Override this method to add custom pre-save behavior.

  ```python
  def before_save(self, *args, **kwargs):
      # Custom pre-save logic here
  ```

- **`after_save(*args, **kwargs)`**  
  Called after an instance of `AbstractLOVValue` is saved. Override this method to add custom post-save behavior.

  ```python
  def after_save(self, *args, **kwargs):
      # Custom post-save logic here
  ```

#### Manager and QuerySet Methods


- **`values_for_tenant(tenant)`**  
  Returns QuerySet of all *available* values for a given tenant, including:
  - all required default values
  - all non-required default values
  - all tenant-specific values for this tenant

- **`selected_values_for_tenant(tenant)`**  
  Returns QuerySet of all *selected* values for a given tenant, including:
  - all required default values
  - all *selected* non-required default values
  - all *selected* tenant-specific values for this tenant

## Management Commands

- `update_lovs`: Synchronizes the `lov_defaults` in each model, if any, with the database.

## Settings

- `LOV_MODEL_BASE`: Defaults to `django.db.models.base.ModelBase`, but can be overridden with a different class as the base for AbstractLOVValue and AbstractLOVSelection models.
