class ModelClassParsingError(Exception):
    """Used when a model class cannot be parsed from the value provided."""

    def __init__(self, message="Model class cannot be parsed from the value provided"):
        self.message = message
        super().__init__(self.message)


class IncorrectSubclassError(Exception):
    """Used when the value of `lov_value_model` is not a subclass of the correct abstract model."""

    def __init__(self, message="Incorrect subclass usage for lov_value_model"):
        self.message = message
        super().__init__(self.message)


class NoTenantProvidedFromViewError(Exception):
    """Used when a view does not pass an lov_tenant instance from the view to a form."""

    def __init__(self, message="The view did not pass an lov_tenant instance to the form"):
        self.message = message
        super().__init__(self.message)
