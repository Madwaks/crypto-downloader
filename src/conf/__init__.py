import os
import importlib
from typing import Tuple, Any
from fnmatch import fnmatch
from core.exceptions import ImproperlyConfigured
from utils.functional import LazyObject, empty
from . import global_settings


ENVIRONMENT_VARIABLE = "APP_SETTINGS_MODULE"


class LazySettings(LazyObject):
    """
    A lazy proxy for either global settings or a custom settings object.
    The user can manually configure settings prior to using them. Otherwise,
    the application uses the settings module pointed to by APP_SETTINGS_MODULE.
    """

    def _setup(self, name=None):
        """
        Load the settings module pointed to by the environment variable. This
        is used the first time settings are needed, if the user hasn't
        configured settings manually.
        """
        settings_module = os.environ.get(ENVIRONMENT_VARIABLE)
        if not settings_module:
            desc = f"setting {name}" if name else "settings"
            raise ImproperlyConfigured(
                f"Requested {desc}, but settings are not configured. "
                f"You must either define the environment variable {ENVIRONMENT_VARIABLE} "
                "or call settings.configure() before accessing settings."
            )
        self._wrapped = Settings(settings_module)

    def __repr__(self):
        # Hardcode the class name as otherwise it yields 'Settings'.
        if self._wrapped is empty:
            return "<LazySettings [Unevaluated]>"
        return f'<LazySettings "{self._wrapped.SETTINGS_MODULE}">'

    def __getattr__(self, name):
        """
        Return the value of a setting and cache it in self.__dict__.
        """
        if self._wrapped is empty:
            self._setup(name)
        val = getattr(self._wrapped, name)
        self.__dict__[name] = val
        return val

    def __setattr__(self, name, value):
        """
        Set the value of setting. Clear all cached values if _wrapped changes
        or clear single values when set.
        """
        if name == "_wrapped":
            self.__dict__.clear()
        else:
            self.__dict__.pop(name, None)
        super().__setattr__(name, value)

    def __delattr__(self, name):
        """
        Delete a setting and clear it from cache if needed.
        """
        super().__delattr__(name)
        self.__dict__.pop(name, None)

    def override_settings(self, **kwargs):
        if self._wrapped is empty:
            raise RuntimeError("Settings not configured.")
        print("Overriding settings at runtime can be dangerous. I hope you know what you're doing!")

        from conf import settings
        for key, value in kwargs.items():
            logger.warning(f"Overriding setting: '{key}'='{value}'")
            # Okay yes, a little overkill...
            # But it ensures the local `settings` module already imported is changed as well as all future imports
            settings._wrapped.__setattr__(key, value)
            self._wrapped.__setattr__(key, value)
            self.__setattr__(key, value)

    def configure(self, default_settings=global_settings, **options):
        """
        Called to manually configure the settings. The 'default_settings'
        parameter sets where to retrieve any unspecified values from (its
        argument must support attribute access (__getattr__)).
        """
        if self._wrapped is not empty:
            raise RuntimeError("Settings already configured.")
        holder = UserSettingsHolder(default_settings)
        for name, value in options.items():
            setattr(holder, name, value)
        self._wrapped = holder

    @property
    def configured(self):
        """
        Return True if the settings have already been configured.
        """
        return self._wrapped is not empty


class Settings:
    def __init__(self, settings_module):
        # update this dict from global settings (but only for ALL_CAPS settings)
        for setting in dir(global_settings):
            if setting.isupper():
                setattr(self, setting, getattr(global_settings, setting))

        # store the settings module in case someone later cares
        self.SETTINGS_MODULE = settings_module

        mod = importlib.import_module(self.SETTINGS_MODULE)

        self._explicit_settings = set()
        for setting in dir(mod):
            if setting.isupper():
                setting_value = getattr(mod, setting)
                setattr(self, setting, setting_value)
                self._explicit_settings.add(setting)

    def is_overridden(self, setting):
        return setting in self._explicit_settings

    def __repr__(self):
        return f'<{self.__class__.__name__} "{self.SETTINGS_MODULE}">'


class UserSettingsHolder:
    """
    Holder for user configured settings.
    """

    # SETTINGS_MODULE doesn't make much sense in the manually configured
    # (standalone) case.
    SETTINGS_MODULE = None

    def __init__(self, default_settings):
        """
        Requests for configuration variables not in this class are satisfied
        from the module specified in default_settings (if possible).
        """
        self.__dict__["_deleted"] = set()
        self.default_settings = default_settings

    def __getattr__(self, name):
        if name in self._deleted:
            raise AttributeError
        return getattr(self.default_settings, name)

    def __setattr__(self, name, value):
        self._deleted.discard(name)
        super().__setattr__(name, value)

    def __delattr__(self, name):
        self._deleted.add(name)
        if hasattr(self, name):
            super().__delattr__(name)

    def __dir__(self):
        return sorted(
            s
            for s in [*self.__dict__, *dir(self.default_settings)]
            if s not in self._deleted
        )

    def is_overridden(self, setting):
        deleted = setting in self._deleted
        set_locally = setting in self.__dict__
        set_on_default = getattr(
            self.default_settings, "is_overridden", lambda s: False
        )(setting)
        return deleted or set_locally or set_on_default

    def __repr__(self):
        return f"<{self.__class__.__name__}>"


class Paths(object):
    def __init__(self, load_from_module: str = ""):
        """
        Loads all path attrs from a given module into the class instance.

        All variables in uppercase are loaded into the class.

        :param load_from_module: string: Loads the module passed as a string using importlib
        """
        try:
            _tmp_paths_module = importlib.import_module(load_from_module)
        except ImportError as e:
            raise ImportError(f"Unable to load module : {e}")
        for attribute in dir(_tmp_paths_module):
            if attribute.isupper():
                path_value = getattr(_tmp_paths_module, attribute)
                setattr(self, attribute, path_value)

    def __iter__(self) -> Tuple:
        """
        Iterates on all attributes (paths) loaded into the class

        :return: Yields a tuple of strings with `key, value` by default, `dict.items()` style
        """
        for attr in dir(self):
            if attr.isupper():
                yield attr, getattr(self, attr)

    def get_items_from_glob(self, glob: str) -> Tuple:
        """
        Iterator on the class but using pattern matching for attribute names

        Uses `fnmatch` builtin lib for POSIX glob syntax (FOO_*.bar)

        :param glob: Pattern passed to fnmatch for matching
        :return: Yields a tuple of strings with `key, value` by default, `dict.items()` style
        """
        for attr, val in self.items():
            if fnmatch(attr, glob):
                yield attr, val

    def get_keys_from_glob(self, glob: str) -> str:
        """
        Replicates `get_items_from_glob()` but only yields the attribute names.

        :param glob: Pattern passed to fnmatch for matching
        :return: Yields a string representing the attribute name, `dict.keys()` style
        """
        for attr, val in self.get_items_from_glob(glob):
            yield attr

    def get_values_from_glob(self, glob: str) -> Any:
        """
        Replicates `get_items_from_glob()` but only yields the attribute values.

        :param glob: Pattern passed to fnmatch for matching
        :return: Yields a string representing the attribute name, `dict.values()` style
        """
        for attr, val in self.get_items_from_glob(glob):
            yield val

    def get_loader_items_from_glob(
        self, glob: str, add_csv: bool = True, add_pickle: bool = False
    ) -> Tuple[Tuple]:
        """
        Utility function used for collection Path information for Loader classes.

        Returns a Tuple of conditional depending on the `add_csv` and `add_pickle` flags
        (from 2 to 4), of tuples of Attribute/Value pairs .
        Uses internal `get_TYPE_from_glob` methods.

        If an element does not exist, it's value inside the returned tuple will be `None`.

        :param glob: Pattern passed to fnmatch for matching
        :param add_csv: If True, add the CSV_PATH attribute
        :param add_pickle: If True, add the PICKLE attribute (requires `add_csv` to also be `True`)
        :return: tuple of conditional size from 2 to 4 of tuples of Attribute/Value pairs
        """
        if add_pickle and not add_csv:
            raise ValueError(
                "Currently add_csv must be `True` if add_pickle is `True`."
            )
        drive_file = drive_sheet = csv_path = pickle_dump = (None, None)
        for attr, val in self.get_items_from_glob(glob):
            if "DRIVE_FILE" in attr:
                drive_file = attr, val
            elif "DRIVE_SHEET" in attr:
                drive_sheet = attr, val
            elif add_csv and "CSV_PATH" in attr:
                csv_path = attr, val
            elif add_pickle and "PICKLE" in attr:
                pickle_dump = attr, val
        loader_items = (drive_file, drive_sheet, csv_path, pickle_dump)
        return (
            loader_items
            if add_pickle
            else (loader_items[:3] if add_csv else loader_items[:2])
        )

    def get_loader_keys_from_glob(
        self, glob: str, add_csv: bool = True, add_pickle: bool = False
    ) -> Tuple[str]:
        """
        Utility function used for collection Path information for Loader classes.

        Returns a Tuple of conditional depending on the `add_csv` and `add_pickle` flags
        (from 2 to 4), of strings corresponding to the collected Attribute names.
        Uses internal `get_TYPE_from_glob` methods.

        If an element does not exist, it's value inside the returned tuple will be `None`.

        :param glob: Pattern passed to fnmatch for matching
        :param add_csv: If True, add the CSV_PATH attribute
        :param add_pickle: If True, add the PICKLE attribute (requires `add_csv` to also be `True`)
        :return: tuple of conditional size from 2 to 4 strings corresponding to the collected Attribute names
        """
        return tuple(
            elem[0]
            for elem in self.get_loader_items_from_glob(
                glob, add_csv=add_csv, add_pickle=add_pickle
            )
        )

    def get_loader_values_from_glob(
        self, glob: str, add_csv: bool = True, add_pickle: bool = False
    ) -> Tuple[Any]:
        """
        Utility function used for collection Path information for Loader classes.

        Returns a Tuple of conditional depending on the `add_csv` and `add_pickle` flags
        (from 2 to 4), of either strings or Path objects representing the collected Values.
        Uses internal `get_TYPE_from_glob` methods.

        If an element does not exist, it's value inside the returned tuple will be `None`.

        :param glob: Pattern passed to fnmatch for matching
        :param add_csv: If True, add the CSV_PATH attribute
        :param add_pickle: If True, add the PICKLE attribute (requires `add_csv` to also be `True`)
        :return: tuple of conditional size from 2 to 4 of strings or Path objects representing the collected Values
        """
        return tuple(
            elem[1]
            for elem in self.get_loader_items_from_glob(
                glob, add_csv=add_csv, add_pickle=add_pickle
            )
        )

    def items(self):
        yield from self

    def keys(self):
        for attr, val in self:
            yield attr

    def values(self):
        for attr, val in self:
            yield val


settings = LazySettings()
