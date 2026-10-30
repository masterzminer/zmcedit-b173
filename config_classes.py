from configparser import RawConfigParser
from pathlib import Path

class Observer:
    def __init__(self, func, name=None):
        self.func = func
        self.name = name

class Setting:
    """Individual object for a setting"""

    def __init__(self, default_value):
        # Store the option type and default value
        self.option_type = type(default_value)
        self.default_value = default_value
        self.observers = []
        """List of functions to run when the value changes"""

        self.section: Section
        """Singleton section which holds this setting"""

    def __set_name__(self, parent, name):
        # On the init for each setting, saving the setting's field name
        self.name = name

    def get(self):
        getters = self.section._getters

        # Get the getter based on the type of the option
        getter = getters.get(self.option_type)
        # Return the actual value from the config
        return getter(self.name)

    @property
    def v(self):
        """shorthand for get"""
        return self.get()

    def __str__(self):
        return str(self.get())

    def __repr__(self):
        return f"name:{self.name}, section:{self.section.NAME}, value:{self.v}, default:{self.default_value}"

    def set(self, value):
        # TODO test that this only sends an update when the value changes
        old = self.get()
        if old == value:
            return

        self.section.set(self.name, value)

        for obs in self.observers:
            obs.func(value)

    def add_observer(self, func, name=None):
        # Skip if the observer already exists
        if name is not None:
            for obs in self.observers:
                if obs.name == name:
                    return
        
        # Add the observer
        self.observers.append(Observer(func, name))


class Section:
    def __init__(self, config: RawConfigParser):
        # Store the config for later
        self._config = config

        def get(fun, v):
            return fun(self.NAME, v)

        # Setup getters, for each type, use the appropriate function from the config
        self._getters = {
            bool: lambda v: get(config.getboolean, v),
            int: lambda v: get(config.getint, v),
            float: lambda v: get(config.getfloat, v),
            str: lambda v: get(config.get, v)
        }

        # Add the section if it's missing
        if not self._config.has_section(self.NAME):
            self._config.add_section(section=self.NAME)

        # Add all the settings if they don't exist
        # Go through each setting name and it's object
        for name, setting in vars(type(self)).items():
            # If the field is a setting and the config doesn't have that option, add it
            if isinstance(setting, Setting):
                # Give this section to the setting
                setting.section = self

                # Add it to the config if needed
                if not self._config.has_option(self.NAME, name):
                    self._config.set(self.NAME, name, str(setting.default_value))

    def set(self, setting, value):
        """Set the given value on the config"""
        self._config.set(self.NAME, setting, value)

    def get(self, setting):
        """Get the given value on the config as a string"""
        return self._config.get(self.NAME, setting)
    
    def get_all(self):
        """Return a list of tuples as (key, value) for all settings"""
        return [
            (name, str(getattr(self, name)))
            for name, setting in vars(type(self)).items()
            if isinstance(setting, Setting)
        ]


class DirectorySetting(Setting):
    """Setting for storing and retrieving a path"""

    def __init__(self, default_value=Path.home()):
        # Store the path as a string
        super().__init__(str(default_value))

    def get(self,):
        return Path(super().get())

    def set(self, value):
        super().set(str(value))