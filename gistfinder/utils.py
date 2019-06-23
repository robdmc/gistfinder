class cached_property(object):
    """
    This is a direct copy-paste of Django's cached property from
    https://github.com/django/django/blob/2456ffa42c33d63b54579eae0f5b9cf2a8cd3714/django/utils/functional.py#L38-50
    """
    def __init__(self, func):
        self.func = func

    def __get__(self, instance, type=None):
        if instance is None:
            return self
        res = instance.__dict__[self.func.__name__] = self.func(instance)
        return res


def print_temp(*args, file_name='/tmp/gistfinder.log'):
    with open(file_name, 'a') as buff:
        print(*args, file=buff)
