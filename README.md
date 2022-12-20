
# flexible-list-of-values

Flexible and Extensible Lists of Values (LOV) for Django

> When adding customizability to a SaaS app, there are a variety of approaches and tools:
> 
> - [Dynamic models](https://baserow.io/blog/how-baserow-lets-users-generate-django-models) and dynamic model fields
> - [Entity-Attribute-Value (EAV)](https://en.wikipedia.org/wiki/Entity%E2%80%93attribute%E2%80%93value_model)
> - Adding [JSONField](https://docs.djangoproject.com/en/4.1/ref/models/fields/#jsonfield) to a model
>
> But these approaches can be a bit *too* flexible. Sometimes we want to provide guardrails for our tenants.
>
> *flexible-list-of-values* provides you a way to give your SaaS app's tenants customization options in its User-facing forms, but also lets you provide them with defaults - either mandatory or optional - to prevent each tenant having to "recreate the wheel".

*Note: The terms "entity" and "tenant" are used interchangeably in this document to refer to a model within your project that has associated Users, and which has "ownership" over the LOV value options provided to its Users*

## Most basic example of flexible-list-of-values setup

```python
class Tenant(models.Model):
    """
    An existing model within your project in the `entities` app to which we are attaching the list of values.
    This is just an example model. Your approach may be different.
    """

# ---
from flexible_list_of_values import AbstractLOVValue, AbstractLOVSelection

class ConcreteLOVValue(AbstractLOVValue):
    """
    Most basic concrete implementation with no default options provided.
    """

    lov_entity_model = Tenant  # The model to which we attach these selections


class ConcreteLOVSelection(AbstractLOVSelection):
    """
    Most basic concrete implementation.
    """

    lov_value_model = ConcreteLOVValue
    lov_entity_model = Tenant  # The model to which we attach these selections
```

Now `Tenant` model instances have a relationship with `ConcreteLOVValue` and `ConcreteLOVSelection`.

---

## Example implementation

Imagine your project provides a contact form that your tenants' visitors use to receive information requests from their potential customers. Now you want to add a "subject" field to this form.

You could hard-code some subject value choices using CharField and choices, or if your tenants wanted the field to be customizable you could use JSONField or other methods.

This package provides an in-between option. You can specify some default options that are required, provide some default options that your tenants can either use or discard, and allow additional custom value options specific to the tenant.

![Descriptive Diagram](https://raw.githubusercontent.com/jacklinke/flexible-list-of-values/main/docs/media/FlexibleLOVDescription.png)

Models:

```python
from flexible_list_of_values import AbstractLOVValue, AbstractLOVSelection


class Tenant(models.Model):
    """
    An existing model within your project in the `entities` app to which we are attaching the list of values.
    Assumes these models exist in the "entities" app, so this model is "entities.Tenant".
    This is just an example model. Your approach may be different.
    """

class TenantSubjectLOVValue(AbstractLOVValue):
    """
    Concrete implementation of AbstractLOVValue with Subject options that a Tenant can select from.
    """

    lov_entity_model = Tenant
    lov_selections_model = "entities.TenantSubjectLOVSelection"

    # Default MANDATORY and OPTIONAL values
    lov_defaults = {
        "Requesting General Information": {"value_type": LOVValueType.MANDATORY},
        "Hours of Operation": {},  # Defaults to MANDATORY
        "Demo Request": {"value_type": LOVValueType.OPTIONAL},
        "Complaint": {"value_type": LOVValueType.OPTIONAL},
    }

    class Meta:
        verbose_name = "Subject Value"
        verbose_name_plural = "Subject Values"


class TenantSubjectLOVSelection(AbstractLOVSelection):
    """
    Concrete implementation of AbstractLOVSelection with actual selections of Subjects for each Tenant
    """

    lov_value_model = TenantSubjectLOVValue  # You can use the actual class model
    lov_entity_model = "entities.Tenant"  # Or you can specify as "app.ModelName"

    class Meta:
        verbose_name = "Subject Selection"
        verbose_name_plural = "Subject Selections"
```

For the example above, in a Contact form for Users of TenantA or TenantB ...

- The `subject` ModelChoiceField will always include Subject choices for "Requesting General Information" and "Hours of Operation".
- Both tenants can choose whether their Users will have the "Demo Request" and "Complaint" choices.
- And both tenants can create custom tenant-specific value options for their Users to choose from.

## Working with LOV Values

View the available Values for this Tenant:

```python
tenant = Tenant.objects.first()
values_for_tenant = TenantSubjectLOVValue.objects.for_entity(tenant)
```

View the selected Values for this Tenant:

```python
tenant = Tenant.objects.first()
values_for_tenant = TenantSubjectLOVValue.objects.for_entity(tenant)
```

Create new custom Values for this Tenant:

```python
tenant = Tenant.objects.first()
TenantSubjectLOVValue.objects.create_for_entity(tenant, "New Value for this Tenant")
```

Delete Values for this Tenant (only deletes custom values owned by this tenant)

```python
tenant = Tenant.objects.first()
values = TenantSubjectLOVValue.objects.for_entity(entity=tenant).filter(name__icontains="Something")
for value in values:
    value.delete()
```


## Letting tenants select LOV value choices for their users

Tenants can select from among the Values available for this Tenant or create new Values

```python
from django.forms.widgets import HiddenInput
from flexible_list_of_values import LOVValueType


class TenantValueCreateForm(forms.ModelForm):
    """
    Form to let a tenant add a new custom LOV Value.
    """
    class Meta:
        model = TenantSubjectLOVValue
        fields = ["name", "lov_entity", "value_type"]

    def __init__(self, *args, **kwargs):
        self.lov_entity = kwargs.pop("lov_entity", None)
        if not self.lov_entity:
            raise NoEntityProvidedFromViewError("No lov_entity model class was provided to the form from the view")
        super().__init__(*args, **kwargs)
        
        # Set the value_type field value to CUSTOM and use a HiddenInput widget
        self.fields['value_type'].widget = HiddenInput()
        self.fields['value_type'].initial = LOVValueType.CUSTOM
        
        # Set the lov_entity field value to the entity instance provided from the view
        #   and use a HiddenInput widget
        self.fields['lov_entity'].widget = HiddenInput()
        self.fields['lov_entity'].initial = self.lov_entity


class value_create_view(request):
    # However you specify the current entity/tenant for the User submitting this form.
    # This is only an example.
    tenant = request.user.tenant

    # Here we provide the User's entity, which the form will use
    form = TenantValueCreateForm(request.POST or None, lov_entity=tenant)
    ...


class TenantValueSelectionForm(forms.ModelForm):
    """
    Form to let a tenant select which LOV Values its users can choose from.
    """
    class Meta:
        model = TenantSubjectLOVSelection
        fields = ["lov_entity", "lov_values"]

    def __init__(self, *args, **kwargs):
        self.lov_entity = kwargs.pop("lov_entity", None)
        super().__init__(*args, **kwargs)

        self.fields["subject"].queryset = ConcreteLOVSelection.objects.values_for_entity(self.lov_entity)


class selection_view(request):
    # However you specify the current entity/tenant for the User submitting this form.
    # This is only an example.
    tenant = request.user.tenant

    # Here we provide the entity 
    form = SelectionForm(request.POST or None, lov_entity=entity)
    ...
```

## Working with a tenant's LOV Selections

Tenant's Users make a choice from among the selected Values for this Tenant each time they fill out a Contact form.

```python
class Contact(models.Model):
    subject = models.ForeignKey(TenantSubjectLOVSelection, on_delete=models.SET_NULL, null=True, blank=True)

    body = models.TextField()


class ContactForm(forms.Form):
    forms.ModelChoiceField(queryset=None)
    
    class Meta:
        model = Contact
        fields = ['__all__']

    def __init__(self, *args, **kwargs):
        self.lov_entity = kwargs.pop("lov_entity", None)
        if not self.lov_entity:
            raise NoEntityProvidedFromViewError("No lov_entity model class was provided to the form from the view")
        super().__init__(*args, **kwargs)

        self.fields["subject"].queryset = ConcreteLOVSelection.objects.selections_for_entity(entity=self.lov_entity)


class contact_view(request):
    # However you specify the current entity/tenant for the User submitting this form.
    # This is only an example.
    tenant = request.user.tenant

    # Here we provide the entity 
    form = ContactForm(request.POST or None, lov_entity=entity)
    ...
```

Here, Users for TenantA who are filling out a Contact form will see all required values, the optional values that TenantA has selected, and any custom values TenantA has created. TenantB's users will see all required values, the optional values that TenantB has selected, and any custom values TenantB has created.

## API

### Model: AbstractLOVValue

#### Fields

- **id**: default id
- **name** (CharField): The name or title of the value to be used.
- **lov_entity** (FK): the owning entity for this value. If this is a default value, this field will be null.
- **lov_associated_entities** (M2M): all entities this value is associated with. (The reverse relationship on the entity model is all values selected for the entity)
- **value_type** (CharField): Any of
    - LOVValueType.MANDATORY
    - LOVValueType.OPTIONAL
    - LOVValueType.CUSTOM
- **deleted** (DateTimeField): The datetime this value was deleted, or null if it is not deleted.


#### Model attributes

<dl>
  <dt>lov_defaults</dt>
  <dd>
    A dictionary of default mandatory and optional values from which an entity can select. See usage examples above.<br>
    <em>Default</em>: <code>{}</code>
  </dd>

  <dt>lov_entity_model</dt>
  <dd>
    Specifies the model class for the 'entity' in your project which can customize its Users' LOVs. Must either be an actual model class (<code>Entity</code>) or the string representation of the model class (<code>"entities.Entity"</code>).<br>
    <em>* Required</em>
  </dd>

  <dt>lov_entity_on_delete</dt>
  <dd>
    What should happen when the related entity instance is deleted.<br>
    <em>Default</em>: <code>models.CASCADE</code>
  </dd>

  <dt>lov_entity_model_related_name</dt>
  <dd>
    <code>related_name</code> for the related entity instance.<br>
    <em>Default</em>: <code>"%(app_label)s_%(class)s_related"</code>
  </dd>

  <dt>lov_entity_model_related_query_name</dt>
  <dd>
    <code>related_query_name</code> for the related entity instance.<br>
    <em>Default</em>: <code>"%(app_label)s_%(class)ss"</code>
  </dd>

  <dt>lov_selections_model</dt>
  <dd>
    Specifies the model class of the through-model between an Entity and a Value. Each instance of this through-model is an option that the tenant's users can choose from. Must be a concrete subclass of AbstractLOVSelection. Must either be an actual model class (e.g.: <code>TenantSubjectLOVSelection</code>) or the string representation of the model class (e.g.: <code>"entities.TenantSubjectLOVSelection"</code>).<br>
    <em>* Required</em>
  </dd>

  <dt>lov_associated_entities_related_name</dt>
  <dd>
    <code>related_name</code> for the M2M to the entity instance.<br>
    <em>Default</em>: <code>"%(app_label)s_%(class)s_selections"</code>
  </dd>

  <dt>lov_associated_entities_related_query_name</dt>
  <dd>
    <code>related_query_name</code> for the M2M to the entity instance.<br>
    <em>Default</em>: <code>"%(app_label)s_%(class)ss_selected"</code>
  </dd>
</dl>

#### Manager and QuerySet Methods

<dl>
  <dt>for_entity(entity)</dt>
  <dd>
    Returns QuerySet of all available values for a given entity, including:<br>
    <ul>
        <li>all required default values</li>
        <li>all non-required default values</li>
        <li>all entity-specific values for this entity</li>
    </ul>
  </dd>

  <dt>create_for_entity(entity, name: str)</dt>
  <dd>
    Creates a new selectable Value for the provided entity.
  </dd>

  <dt>create_mandatory(name: str)</dt>
  <dd>
    Creates a new Value (selected for all entities).
  </dd>

  <dt>create_optional(name: str)</dt>
  <dd>
    Creates a new selectable optional Value (selectable by all entities).
  </dd>
</dl>


### Model: AbstractLOVSelection

This is a through-model from an concrete LOVValue model instance to an entity model instance representing the value selections an entity has made.

#### Fields

- **id**: default id
- **lov_entity** (FK): the entity this selection is associated with.
- **lov_value** (FK): the value this selection is associated with.

#### Model attributes

<dl>
  <dt>lov_entity_model</dt>
  <dd>
    Specifies the model class for the 'entity' in your project which can customize its Users' LOVs. Must either be an actual model class (<code>Entity</code>) or the string representation of the model class (<code>"entities.Entity"</code>).<br>
    <em>* Required</em>
  </dd>

  <dt>lov_entity_on_delete</dt>
  <dd>
    What should happen when the related entity instance is deleted.<br>
    <em>Default</em>: <code>models.CASCADE</code>
  </dd>

  <dt>lov_entity_model_related_name</dt>
  <dd>
    <code>related_name</code> for the related entity instance.<br>
    <em>Default</em>: <code>"%(app_label)s_%(class)s_related"</code>
  </dd>

  <dt>lov_entity_model_related_query_name</dt>
  <dd>
    <code>related_query_name</code> for the related entity instance.<br>
    <em>Default</em>: <code>"%(app_label)s_%(class)ss"</code>
  </dd>


  <dt>lov_value_model</dt>
  <dd>
    Specifies the model class for the concrete (not abstract!) subclass of AbstractLOVValue. Must either be an actual model class (<code>TenantSubjectLOVSelection</code>) or the string representation of the model class (<code>"contacts.TenantSubjectLOVSelection"</code>).<br>
    <em>* Required</em>
  </dd>

  <dt>lov_value_model_related_name</dt>
  <dd>
    <code>related_name</code> for the related concrete subclassed AbstractLOVValue instance.<br>
    <em>Default</em>: <code>"%(app_label)s_%(class)s_related"</code>
  </dd>

  <dt>lov_value_model_related_query_name</dt>
  <dd>
    <code>related_query_name</code> for the related concrete subclassed AbstractLOVValue instance.<br>
    <em>Default</em>: <code>"%(app_label)s_%(class)ss"</code>
  </dd>
</dl>

#### Manager and QuerySet Methods

<dl>
  <dt>values_for_entity(entity)</dt>
  <dd>
    Returns QuerySet of all <em>available</em> values for a given entity, including:<br>
    <ul>
        <li>all required default values</li>
        <li>all non-required default values</li>
        <li>all entity-specific values for this entity</li>
    </ul>
  </dd>
  
  <dt>selections_for_entity(entity)</dt>
  <dd>
    Returns QuerySet of all <em>selected</em> values for a given entity, including:<br>
    <ul>
        <li>all required default values</li>
        <li>all selected non-required default values</li>
        <li>all selected entity-specific values for this entity</li>
    </ul>
  </dd>
</dl>
