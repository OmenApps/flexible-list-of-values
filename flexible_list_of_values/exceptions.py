class ModelClassParsingError(Exception):
    """
    Used when a model class cannot be parsed from the value provided
    """
    pass


class IncorrectSubclassError(Exception):
    """
    Used when the value of `lov_value_model` is not a subclass of the correct abstract model
    """
    pass


class NoEntityProvidedFromViewError(Exception):
    """
    Used when a view does not pass an lov_entity instance from the view to a form
    """
    pass
