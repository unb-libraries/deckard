"""Provides a function to load a class from a module."""
def load_class(
        module_name: str,
        class_name: str,
        args: list=[]
) -> object:
    """Loads a class from a module.

    Args:
        module_name (str): The name of the module.
        class_name (str): The name of the class.
        args (list): The arguments to pass to the class constructor.

    Returns:
        object: The class instance.
    """
    m = __import__(
        module_name,
        fromlist=['']
    )
    c = getattr(m, class_name)
    return c(*args)
