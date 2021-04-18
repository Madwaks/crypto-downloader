import sys
import copy
import operator
import time
import threading
import hashlib
from typing import Any, Callable

empty = object()


def constant_hash(string: str) -> int:
    return int(hashlib.md5(string.encode()).hexdigest(), 16)


def run_force_timeout(func: Callable, *args, timeout_seconds: int = 1, default_return: Any = None, **kwargs):
    import signal

    def handler(signum, frame):
        raise TimeoutError()

    # set the timeout handler
    signal.signal(signal.SIGALRM, handler)
    signal.alarm(timeout_seconds)
    try:
        result = func(*args, **kwargs)
    except TimeoutError:
        result = default_return
    finally:
        signal.alarm(0)

    return result


def wait_for_thread_finish(func: Callable, *args, op_timeout: int = 15, chk_interval: float = 0.1, **kwargs) -> Any:
    """ Wait for a multithreading function call to finish.
    Do not use for daemon threads at risk of lock if timeout is disabled.

    :param func: Function to call that will use threading
    :param args: All args that will be passed trasparently to the `func` callable.
    :param op_timeout: Forced timeout in seconds in order to continue process regardless. If <= 0, timeout is disabled.
    :param chk_interval: Interval in seconds for the sleep call between each check for finished thread.
    :param kwargs: All remaining kwargs will be passed transparently to the `func` callable.
    :return: Return value is that of the `func` callable.
    """
    thread_count = threading.active_count()
    res = func(*args, **kwargs)
    start = time.time()
    while threading.active_count() > thread_count and (op_timeout <= 0 or time.time() - start < op_timeout):
        time.sleep(chk_interval)

    return res


def get_object_size(obj: object, seen: set = None):
    """
    Recursively finds size of objects in bytes
    """
    size = sys.getsizeof(obj)
    if seen is None:
        seen = set()
    obj_id = id(obj)
    if obj_id in seen:
        return 0
    # Important mark as seen *before* entering recursion to gracefully handle
    # self-referential objects
    seen.add(obj_id)
    if isinstance(obj, dict):
        size += sum([get_object_size(value, seen) for value in obj.values()])
        size += sum([get_object_size(key, seen) for key in obj.keys()])
    elif hasattr(obj, "__dict__"):
        size += get_object_size(obj.__dict__, seen)
    elif hasattr(obj, "__iter__") and not isinstance(obj, (str, bytes, bytearray)):
        size += sum([get_object_size(elem, seen) for elem in obj])
    return size


def convert_bytes_to_best_unit(size: int):
    units = ("B", "kB", "MB", "GB")
    power = 0
    for power in range(0, len(units)):
        if size < 1000:
            break
        size /= 1000
    return f"{size} {units[power]}"


def get_verbose_object_size(obj: object, true_size: bool = False):
    size = get_object_size(obj) if true_size else sys.getsizeof(obj)
    return convert_bytes_to_best_unit(size)


def module_to_dict(module, omittable=lambda k: k.startswith("_") or not k.isupper()):
    """Convert a module namespace to a Python dictionary."""
    return {k: repr(getattr(module, k)) for k in dir(module) if not omittable(k)}


def new_method_proxy(func):
    def inner(self, *args):
        if self._wrapped is empty:
            self._setup()
        return func(self._wrapped, *args)

    return inner


def convert_to_bool(arg: Any):
    if isinstance(arg, (bool, int)):
        return bool(arg)
    if not arg:
        return False
    arg = arg.strip().lower()
    if arg in ("false", "no"):
        return False
    return True


class LazyObject:
    """
    A wrapper for another class that can be used to delay instantiation of the
    wrapped class.
    By subclassing, you have the opportunity to intercept and alter the
    instantiation.
    """

    # Avoid infinite recursion when tracing __init__ (#19456).
    _wrapped = None

    def __init__(self):
        # Note: if a subclass overrides __init__(), it will likely need to
        # override __copy__() and __deepcopy__() as well.
        self._wrapped = empty

    __getattr__ = new_method_proxy(getattr)

    def __setattr__(self, name, value):
        if name == "_wrapped":
            # Assign to __dict__ to avoid infinite __setattr__ loops.
            self.__dict__["_wrapped"] = value
        else:
            if self._wrapped is empty:
                self._setup()
            setattr(self._wrapped, name, value)

    def __delattr__(self, name):
        if name == "_wrapped":
            raise TypeError("can't delete _wrapped.")
        if self._wrapped is empty:
            self._setup()
        delattr(self._wrapped, name)

    def _setup(self):
        """
        Must be implemented by subclasses to initialize the wrapped object.
        """
        raise NotImplementedError("subclasses of LazyObject must provide a _setup() method")

    # Because we have messed with __class__ below, we confuse pickle as to what
    # class we are pickling. We're going to have to initialize the wrapped
    # object to successfully pickle it, so we might as well just pickle the
    # wrapped object since they're supposed to act the same way.
    #
    # Unfortunately, if we try to simply act like the wrapped object, the ruse
    # will break down when pickle gets our id(). Thus we end up with pickle
    # thinking, in effect, that we are a distinct object from the wrapped
    # object, but with the same __dict__. This can cause problems (see #25389).
    #
    # So instead, we define our own __reduce__ method and custom unpickler. We
    # pickle the wrapped object as the unpickler's argument, so that pickle
    # will pickle it normally, and then the unpickler simply returns its
    # argument.
    def __reduce__(self):
        if self._wrapped is empty:
            self._setup()
        return unpickle_lazyobject, (self._wrapped,)

    def __copy__(self):
        if self._wrapped is empty:
            # If uninitialized, copy the wrapper. Use type(self), not
            # self.__class__, because the latter is proxied.
            return type(self)()
        else:
            # If initialized, return a copy of the wrapped object.
            return copy.copy(self._wrapped)

    def __deepcopy__(self, memo):
        if self._wrapped is empty:
            # We have to use type(self), not self.__class__, because the
            # latter is proxied.
            result = type(self)()
            memo[id(self)] = result
            return result
        return copy.deepcopy(self._wrapped, memo)

    __bytes__ = new_method_proxy(bytes)
    __str__ = new_method_proxy(str)
    __bool__ = new_method_proxy(bool)

    # Introspection support
    __dir__ = new_method_proxy(dir)

    # Need to pretend to be the wrapped class, for the sake of objects that
    # care about this (especially in equality tests)
    __class__ = property(new_method_proxy(operator.attrgetter("__class__")))
    __eq__ = new_method_proxy(operator.eq)
    __lt__ = new_method_proxy(operator.lt)
    __gt__ = new_method_proxy(operator.gt)
    __ne__ = new_method_proxy(operator.ne)
    __hash__ = new_method_proxy(hash)

    # List/Tuple/Dictionary methods support
    __getitem__ = new_method_proxy(operator.getitem)
    __setitem__ = new_method_proxy(operator.setitem)
    __delitem__ = new_method_proxy(operator.delitem)
    __iter__ = new_method_proxy(iter)
    __len__ = new_method_proxy(len)
    __contains__ = new_method_proxy(operator.contains)


def unpickle_lazyobject(wrapped):
    """
    Used to unpickle lazy objects. Just return its argument, which will be the
    wrapped object.
    """
    return wrapped
