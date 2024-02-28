def load_class(module_name, class_name, args=[]):
    m = __import__(
        module_name + '.' + class_name,
        fromlist=['']
    )
    c = getattr(m, class_name)
    return c(*args)
