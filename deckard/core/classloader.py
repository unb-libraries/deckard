"""

"""

def load_class(
        module_name: str,
        class_name: str,
        args: list=[]
) -> object:
    m = __import__(
        module_name,
        fromlist=['']
    )
    c = getattr(m, class_name)
    return c(*args)
