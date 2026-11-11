from __future__ import annotations
from configparser import RawConfigParser
from pathlib import Path
import json
import log

class Observer:
    def __init__(self, func, name=None):
        self.func = func
        self.name = name

class Setting:
    """Individual object for a setting"""

    def __init__(self, default_value, min=None, max=None):
        # Store the option type and default value
        self.option_type = type(default_value)
        self.default_value = default_value
        self.observers = []
        """List of functions to run when the value changes"""

        self.min = min
        self.max = max

        self.section: Section
        """Singleton section which holds this setting"""

    def __set_name__(self, parent, name):
        # On the init for each setting, saving the setting's field name
        if issubclass(parent, Section):
            self.name = name

    def get(self):
        getters = self.section._getters

        # Get the getter based on the type of the option
        getter = getters.get(self.option_type)
        # Return the actual value from the config
        return getter(self.name)
    
    @property
    def id(self):
        """returns a unique identifier for this config"""
        return self.name + "_" + self.section.NAME


    @property
    def v(self):
        """shorthand for get"""
        return self.get()

    def __str__(self):
        return str(self.get())

    def __repr__(self):
        return f"name:{self.name}, section:{self.section.NAME}, value:{self.v}, default:{self.default_value}"

    def set(self, value):
        old = self.get()
        if old == value:
            return

        # Update the value to be in range if applicable
        if self.min is not None and self.min > value:
            value = self.min
        if self.max is not None and self.max < value:
            value = self.max

        self.section.set(self.name, value)

        for obs in self.observers:
            obs.func(value)

    def add(self, num):
        """used for numeric settings, sets this setting to the current amount plus the given amount"""
        self.set(self.v + num)

    def invert(self):
        """used for boolean settings, sets this setting to the inverted boolean value"""
        self.set(not self.get())

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
        self.NAME: str

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
        self._config.set(self.NAME, setting, str(value))

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
        
    def get_settings(self):
        """Return a list of tuples as (key, settings object) for all settings"""
        return [
            (name, getattr(self, name))
            for name, setting in vars(type(self)).items()
            if isinstance(setting, Setting)
        ]

    def get_from_value(self, value):
        """get a setting that has the given value, returns an arbitrary element if more than one setting has the value, or None if none match"""
        entries = [entry[1] for entry in self.get_settings() if entry[1].v == value]
        if len(entries) == 0:
            return None
        return entries[0]


class DirectorySetting(Setting):
    """Setting for storing and retrieving a path"""

    def __init__(self, default_value=Path.home()):
        # Store the path as a string
        super().__init__(str(default_value))

    def get(self):
        return Path(super().get())

    def set(self, value):
        super().set(str(value))


class IndexSetting(Setting):
    """A setting that has a built in index value associated with it"""

    def __init__(self, default_value, index: int):
        super().__init__(default_value)
        self.index = index


class KeySetting(Setting):
    """A setting for a key binding, mods should be some of ctrl, alt, shift"""

    def __init__(self, default_value, mods = []):
        super().__init__(default_value)
        self.mods = mods

    def mods_match(self, other: KeySetting):
        return set(self.mods) == set(other.mods)

class KeyIndexSetting(IndexSetting):
    """An index setting for a key binding, mods should be some of ctrl, alt, shift"""

    def __init__(self, default_value, index: int, mods = []):
        super().__init__(default_value, index=index)
        self.mods = mods

    def mods_match(self, other: KeySetting):
        return set(self.mods) == set(other.mods)


class ListSection(Section):
    """Section that stores a list of values. Simple implementation for small lists. Can implement as something less brute force if this needs to work with huge lists"""

    def __init__(self, max_size: int, config: RawConfigParser, default_values=[]):
        super().__init__(config)

        self._settings_cache = {}
        """Static object references to settings at specific indexes"""
        
        self.max_size = max_size

        # Get the existing indexes
        indexes = [int(v[0]) for v in self._config.items(self.NAME)]

        new = self.get_list()
        # Check each index for the default values

        for (i, v) in enumerate(default_values):
            # If the list isn't long enough, the list needs to expand
            if i >= len(new):
                new.append(v)
            # If there isn't a value at that index, the default value needs to be inserted
            elif i not in indexes:
                new.insert(i, v)
            # Otherwise, that is now the value if there isn't one there
            else:
                if new[i] == "" or new[i] is None:
                    new[i] = v

        # Update with the new values
        self.set_list(new)

    def set(self, setting, value):
        super().set(setting, value)
        self._check_build_setting(setting, value)

    def _check_build_setting(self, index, value):
        index = str(index)
        if index not in self._settings_cache:
            s = self._settings_cache[index] = Setting(value)
            s.name = index
            s.section = self
        return self._settings_cache[index]

    def get_all(self):
        """Return a list of tuples as (key, value) for all settings"""
        return [(str(i), v) for (i, v) in enumerate(self.get_list())]
    
    def get_settings(self):
        """Return a list of tuples as (key, settings object) for all settings"""
        new_list = []
        for (i, v) in enumerate(self.get_list()):
            setting = self._check_build_setting(i, v)
            new_list.append((i, setting))

        return new_list

    def get_list(self):
        """All values in the list"""

        # Get all values for the section
        values = self._config.items(self.NAME)

        # Sort the values by their key ascending
        values = sorted(values, key=lambda v: v[0])

        # Get just the value itself, not the key
        return [value[1] for value in values]

    def list_index_from_value(self, value):
        values = self.get_list()
        for (i, v) in enumerate(values):
            if v == value:
                return i
        return None
    
    def set_list(self, value):
        """Overwrite all elements in the list"""
        
        # Limit to the max size input
        new_values = value[:self.max_size]

        # Remove all existing values
        old_keys = [entry[0] for entry in self._config.items(self.NAME)]
        for k in old_keys:
            self._config.remove_option(self.NAME, k)

        # Update each value
        for i, v in enumerate(new_values):
            self.set(str(i), v)

    def get_from_index(self, index: int):
        """get the setting in the list of the given index, or null if none exists"""
        values = self.get_list()
        if index >= len(values):
            return None
        return values[index]


class JsonSetting(Setting):
    """A section with utilities for loading and saving raw strings as json"""

    def get(self):
        """returns a dict of the json of this setting"""
        j = super().get()
        if j == "" or j == '""':
            j = r"{}"
        try:
            return json.loads(j)
        except:
            # If it failed to load, use an empty map
            return {}

    def set(self, d):
        """Sets the value of this setting to the given dict as a string with no new lines"""
        if d == "" or d is None:
            d = {}

        # If it isn't valid json, don't set anything
        new_json = None
        try:
            new_json = json.dumps(d, indent=2)
        except:
            log.error(f"Failed to parse json for section: {self.section.NAME}, field: {self.name}")
            return

        super().set(new_json)