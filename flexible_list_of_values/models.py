import logging

from django.apps import apps
from django.core.exceptions import ValidationError
from django.db import models, IntegrityError, transaction
from django.db.models import Q
from django.db.models.constraints import CheckConstraint, UniqueConstraint
from django.db.models.functions import Lower
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from . import LOVValueType
from .app_settings import LOV_MODEL_BASE as ModelBase
from .exceptions import IncorrectSubclassError

logger = logging.getLogger(__name__)


class LOVTenantModelBase(ModelBase):
    """
    Models extending LOVTenantModelBase get a ForeignKey to the model class specified in lov_tenant_model
    """

    def __new__(cls, name, bases, attrs, **kwargs):
        try:
            model = super().__new__(cls, name, bases, attrs, **kwargs)

            for base in bases:
                if base.__name__ == "AbstractLOVSelection" or base.__name__ == "AbstractLOVValue":
                    ConcreteLOVModel = model

                    if not ConcreteLOVModel._meta.abstract and ConcreteLOVModel.lov_tenant_model is not None:
                        ConcreteLOVModel.add_to_class(
                            "lov_tenant",
                            models.ForeignKey(
                                ConcreteLOVModel.lov_tenant_model,
                                on_delete=ConcreteLOVModel.lov_tenant_on_delete,
                                related_name=ConcreteLOVModel.lov_tenant_model_related_name,
                                related_query_name=ConcreteLOVModel.lov_tenant_model_related_query_name,
                                blank=True,
                                null=True,
                            ),
                        )
                    else:
                        raise IncorrectSubclassError(
                            "lov_value_model must be specified for concrete subclasses of AbstractLOVSelection"
                        )

            return model
        except IncorrectSubclassError as e:
            logger.error(f"Incorrect subclass usage in {name}: {e.message}")
            raise e


class LOVValueModelBase(LOVTenantModelBase):
    """
    Models extending TenantAndValueModelBase get a ForeignKey to the model class specified in lov_tenant_model
        (inherited from LOVTenantModelBase), and a ManyToManyField to the model specified in lov_value_model

    Used to set up the ManyToManyField from concrete classes of AbstractLOVSelection
        to concrete classes of AbstractLOVValue.

    Within the model, set the `lov_value_model` parameter to the concrete class inheriting AbstractLOVValue
        and `lov_tenant_model` to the model tenant which is associated with both LOV concrete classes.

        For instance:

            class ConcreteLOVValue(AbstractLOVValue):
                lov_tenant_model = SomeModel
                # or `lov_tenant_model = "myapp.SomeModel"`

            class ConcreteLOVSelection(AbstractLOVSelection):
                lov_value_model = ConcreteLOVValue
                # or `lov_value_model = "myapp.ConcreteLOVValue"`

                lov_tenant_model = SomeModel
                # or `lov_tenant_model = "myapp.SomeModel"`
    """

    def __new__(cls, name, bases, attrs, **kwargs):
        model = super().__new__(cls, name, bases, attrs, **kwargs)

        for base in bases:
            if base.__name__ == "AbstractLOVValue":
                ConcreteLOVValueModel = model

                if (
                    not ConcreteLOVValueModel._meta.abstract
                    and ConcreteLOVValueModel.lov_selections_model is not None
                    and ConcreteLOVValueModel.lov_tenant_model is not None
                ):
                    ConcreteLOVValueModel.add_to_class(
                        "lov_associated_tenants",
                        models.ManyToManyField(
                            ConcreteLOVValueModel.lov_tenant_model,
                            through=ConcreteLOVValueModel.lov_selections_model,
                            through_fields=("lov_value", "lov_tenant"),
                            related_name=ConcreteLOVValueModel.lov_associated_tenants_related_name,  # "selected"
                            related_query_name=ConcreteLOVValueModel.lov_associated_tenants_related_query_name,
                        ),
                    )
                else:
                    raise IncorrectSubclassError(
                        "lov_value_model must be specified for concrete subclasses of AbstractLOVValue"
                    )

        return model


class LOVSelectionModelBase(LOVTenantModelBase):
    """
    Models extending TenantAndValueModelBase get a ForeignKey to the model class specified in lov_tenant_model
        (inherited from LOVTenantModelBase), and a ManyToManyField to the model specified in lov_value_model

    Used to set up the ManyToManyField from concrete classes of AbstractLOVSelection
        to concrete classes of AbstractLOVValue.

    Within the model, set the `lov_value_model` parameter to the concrete class inheriting AbstractLOVValue
        and `lov_tenant_model` to the model tenant which is associated with both LOV concrete classes.

        For instance:

            class ConcreteLOVValue(AbstractLOVValue):
                lov_tenant_model = SomeModel
                # or `lov_tenant_model = "myapp.SomeModel"`

            class ConcreteLOVSelection(AbstractLOVSelection):
                lov_value_model = ConcreteLOVValue
                # or `lov_value_model = "myapp.ConcreteLOVValue"`

                lov_tenant_model = SomeModel
                # or `lov_tenant_model = "myapp.SomeModel"`
    """

    def __new__(cls, name, bases, attrs, **kwargs):
        model = super().__new__(cls, name, bases, attrs, **kwargs)

        for base in bases:
            if base.__name__ == "AbstractLOVSelection":
                ConcreteLOVSelectionModel = model

                if (
                    not ConcreteLOVSelectionModel._meta.abstract
                    and ConcreteLOVSelectionModel.lov_value_model is not None
                ):
                    ConcreteLOVSelectionModel.add_to_class(
                        "lov_value",
                        models.ForeignKey(
                            ConcreteLOVSelectionModel.lov_value_model,
                            on_delete=ConcreteLOVSelectionModel.lov_value_on_delete,
                            related_name=ConcreteLOVSelectionModel.lov_value_model_related_name,
                            related_query_name=ConcreteLOVSelectionModel.lov_value_model_related_query_name,
                            blank=True,
                            null=True,
                        ),
                    )
                else:
                    raise IncorrectSubclassError(
                        "lov_value_model must be specified for concrete subclasses of AbstractLOVValue"
                    )

        return model


class LOVValueQuerySet(models.QuerySet):
    """
    Custom QuerySet for LOVValue models
    """

    def for_tenant(self, tenant):
        """
        Returns all available values for a given tenant, including:
        - all required default values
        - all non-required default values
        - all tenant-specific values for this tenant
        """
        return self.model.objects.filter(
            Q(value_type=LOVValueType.MANDATORY)
            | Q(value_type=LOVValueType.OPTIONAL)
            | Q(value_type=LOVValueType.CUSTOM, lov_tenant=tenant)
        )


class LOVValueManager(models.Manager):
    """
    Custom Manager for LOVValue models
    """

    def get_queryset(self):
        return super().get_queryset().filter(deleted__isnull=True)
    
    
    def before_create(self, *args, **kwargs):
        """
        Hook method called before creating a new instance.
        Can be overridden in subclasses for custom behavior.
        """
        pass

    def after_create(self, obj, *args, **kwargs):
        """
        Hook method called after a new instance is created.
        Can be overridden in subclasses for custom behavior.
        """
        pass

    def create_for_tenant(self, tenant, name: str):
        """Provided an tenant and a value name, creates the new value for that tenant"""
        self.before_create(tenant=tenant, name=name)
        obj = self.create(lov_tenant=tenant, name=name, value_type=LOVValueType.CUSTOM)
        self.after_create(obj, tenant=tenant, name=name)
        return obj

    def create_mandatory(self, name: str):
        """Provided a value name, creates the new value (selected for all tenants)"""
        self.create(name=name, value_type=LOVValueType.MANDATORY)

    def create_optional(self, name: str):
        """Provided a value name, creates the new optional value (selectable by all tenants)"""
        self.create(name=name, value_type=LOVValueType.OPTIONAL)        
    
    def _create_default_option(self, item_name, item_values_dict):
        """Create a default option for a given item_name and item_values_dict.
        
        It should not be necessary, but this method can be overridden in a subclassed Manager
          if you need to modify how subclassed concrete instances are created.
        """
        try:
            with transaction.atomic():
                value_type = item_values_dict.get("value_type", LOVValueType.MANDATORY)

                if value_type not in [LOVValueType.MANDATORY, LOVValueType.OPTIONAL]:
                    raise ValueError(
                        f"LOVValue defaults must be of type `LOVValueType.MANDATORY` or `LOVValueType.OPTIONAL`. "
                        f"For {item_name} you specified value_type = {value_type}.")

                obj, created = self.model.objects.update_or_create(
                    name=item_name,
                    defaults={'value_type': value_type},
                )
                return obj, created
        except IntegrityError as e:
            # Handle the integrity error, e.g., log it or raise a custom exception
            logger.error(f"Integrity error while creating default option '{item_name}': {e}")
            raise

    def _import_defaults(self):
        """
        Get the default values from `Model.objects.defaults` and then create instances
           if they do not already exist or update if values have changed.

        Example:
            lov_defaults = {
                "Cereal_and_Grass": {"value_type": LOVValueType.MANDATORY},              # Creates a mandatory instance
                "Cereal_and_Grass__Alfalfa_Hay": {},                                     # Creates a mandatory instance
                "Cereal_and_Grass__Alfalfa_Seed": {"value_type": LOVValueType.OPTIONAL}, # Creates an optional instance
            }

        Note, it is not necessary to specify `{"value_type": LOVValueType.MANDATORY}` since options are
            mandatory by default. You could set the dict to `{}` and the value model instance will be
            set to mandatory.
        """
        for item_name, item_values_dict in self.model.lov_defaults.items():
            try:
                self.model.objects._create_default_option(item_name, item_values_dict)
            except Exception as e:
                logger.error(f"Error importing default '{item_name}': {e}")
                

class AbstractLOVValue(models.Model, metaclass=LOVValueModelBase):
    """
    Abstract model for defining all available List of Value options.

    Options which are provided by default through model configuration may be Mandatory or Optional

    Using `instance.delete()` only soft-deletes the option
    """

    lov_defaults = {}

    lov_tenant_model = None
    lov_tenant_on_delete = models.CASCADE
    lov_tenant_model_related_name = "%(app_label)s_%(class)s_related"
    lov_tenant_model_related_query_name = "%(app_label)s_%(class)ss"

    lov_selections_model = None

    lov_associated_tenants_related_name = "%(app_label)s_%(class)s_selections"
    lov_associated_tenants_related_query_name = "%(app_label)s_%(class)ss_selected"

    value_type = models.CharField(
        _("Option Type"),
        choices=LOVValueType.choices,
        default=LOVValueType.OPTIONAL,
        max_length=3,
        blank=True,
    )

    name = models.CharField(_("Value Name"), max_length=100)
    deleted = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_("When was this value deleted?"),
    )

    CombinedLOVValueManager = LOVValueManager.from_queryset(LOVValueQuerySet)
    objects = CombinedLOVValueManager()
    unscoped = models.Manager()

    class Meta:
        verbose_name = _("List of Values Option")
        verbose_name_plural = _("List of Values Options")
        constraints = [
            # A particular tenant cannot have more than one value with the same name
            UniqueConstraint(
                Lower("name"),
                "lov_tenant",
                name="%(app_label)s_%(class)s_name_val",
            ),
            # Values of type LOVValueType.CUSTOM must have a specified tenant
            # Values of type LOVValueType.MANDATORY and LOVValueType.OPTIONAL must not have a specified tenant
            CheckConstraint(
                check=Q(value_type=LOVValueType.CUSTOM, lov_tenant__isnull=False)
                | Q(value_type=LOVValueType.MANDATORY, lov_tenant__isnull=True)
                | Q(value_type=LOVValueType.OPTIONAL, lov_tenant__isnull=True),
                name="%(app_label)s_%(class)s_no_mandatory_tenant",
            ),
        ]
        abstract = True

    def delete(self, using=None, keep_parents=False, override=False):
        """
        Soft-delete options to prevent referencing an option that no longer exists
        """
        if self.value_type == LOVValueType.CUSTOM or override:
            self.deleted = timezone.now()
            self.save()

    def __str__(self):
        return self.name

    @classmethod
    def get_concrete_subclasses(cls):
        """
        Return a list of model classes which are subclassed from AbstractLOVValue and
            are not themselves Abstract
        """
        result = []
        for model in apps.get_models():
            if issubclass(model, cls) and model is not cls and not model._meta.abstract:
                result.append(model)
        return result
    
    def before_save(self, *args, **kwargs):
        """
        Hook method called before saving an instance.
        Subclasses can override this to add custom pre-save behavior.
        """
        pass

    def after_save(self, *args, **kwargs):
        """
        Hook method called after saving an instance.
        Subclasses can override this to add custom post-save behavior.
        """
        pass
    
    def save(self, *args, **kwargs):
        """Call full_clean() before saving"""
        self.full_clean()
        self.before_save(*args, **kwargs)
        super().save(*args, **kwargs)
        self.after_save(*args, **kwargs)

    def clean(self):
        """Check that the model is configured correctly."""
        if self.lov_tenant_model is None:
            raise ValidationError("LOV tenant model cannot be None.")
        if self.lov_selections_model is None:
            raise ValidationError("LOV selections model cannot be None.")


class LOVSelectionQuerySet(models.QuerySet):
    """
    Custom QuerySet for LOVSelection models
    """


class LOVSelectionManager(models.Manager):
    """
    Custom Manager for LOVSelection models
    """

    def get_queryset(self):
        return super().get_queryset()

    def values_for_tenant(self, tenant):
        """
        Returns a QuerySet of the AbstractLOVValue subclassed model with all *available*
          values for a given tenant, including:

        - all required default values
        - all non-required default values
        - all tenant-specific values
        """
        try:
            ValuesModel = apps.get_model(self.model.lov_value_model)
            return ValuesModel.objects.for_tenant(tenant=tenant)
        except LookupError:
            # no such model in this application
            return None

    def selected_values_for_tenant(self, tenant):
        """
        Returns a QuerySet of the AbstractLOVValue subclassed model with all *selected*
          values for a given tenant, including:

        - all mandatory default values
        - all tenant-selected optional default values
        - all tenant-selected custom values
        """

        try:
            ValuesModel = apps.get_model(self.model.lov_value_model)

            # Return all Mandatory LOVValue instances
            mandatory = {
                "value_type": LOVValueType.MANDATORY,
            }

            # For LOVSelections that are Optional and belong to our tenant, return the associated LOVValue instances
            optional = {
                "value_type": LOVValueType.OPTIONAL,
                "lov_associated_tenants": tenant,
            }

            # For LOVSelections that are Custom and belong to our tenant, return the associated LOVValue instances
            custom = {
                "value_type": LOVValueType.CUSTOM,
                "lov_associated_tenants": tenant,
            }

            return ValuesModel.objects.filter(Q(**mandatory) | Q(**optional) | Q(**custom))

        except LookupError:
            # no such model in this application
            return None


class AbstractLOVSelection(models.Model, metaclass=LOVSelectionModelBase):
    """
    Identifies all selected LOV Values for a given tenant, which it's users can then choose from

    A single tenant can select multiple LOV Options
    """

    lov_tenant_model = None
    lov_tenant_on_delete = models.CASCADE
    lov_tenant_model_related_name = "%(app_label)s_%(class)s_related"
    lov_tenant_model_related_query_name = "%(app_label)s_%(class)ss"

    lov_value_model = None
    lov_value_on_delete = models.CASCADE
    lov_value_model_related_name = "%(app_label)s_%(class)s_related"
    lov_value_model_related_query_name = "%(app_label)s_%(class)ss"

    CombinedLOVSelectionManager = LOVSelectionManager.from_queryset(LOVSelectionQuerySet)
    objects = CombinedLOVSelectionManager()
    unscoped = models.Manager()

    class Meta:
        verbose_name = _("List of Values Selection")
        verbose_name_plural = _("List of Values Selections")
        constraints = [
            UniqueConstraint(
                "lov_tenant",
                "lov_value",
                name="%(app_label)s_%(class)s_name_val",
            ),
        ]
        abstract = True
        
    def before_save(self, *args, **kwargs):
        """
        Hook method called before saving an instance.
        Subclasses can override this to add custom pre-save behavior.
        """
        pass

    def after_save(self, *args, **kwargs):
        """
        Hook method called after saving an instance.
        Subclasses can override this to add custom post-save behavior.
        """
        pass
    
    def save(self, *args, **kwargs):
        """Call full_clean() before saving"""
        self.full_clean()
        self.before_save(*args, **kwargs)
        super().save(*args, **kwargs)
        self.after_save(*args, **kwargs)

    def clean(self):
        """Check that the model is configured correctly."""
        if self.lov_tenant_model is None:
            raise ValidationError("LOV tenant model cannot be None.")
        if self.lov_value_model is None:
            raise ValidationError("LOV value model cannot be None.")
