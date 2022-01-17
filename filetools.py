import importlib

def class_for_name(module_name, class_name, obj_name, params, *args):
    # Introspection
    # load the module, will raise ImportError if module cannot be loaded
    m = importlib.import_module(module_name + '.' + class_name)
    # get the class, will raise AttributeError if class cannot be found
    c = getattr(m, class_name)
    return c(obj_name, params, *args)
