"""
Configurable settings for rcsb-api

These settings can be overridden at runtime.

For example, you can turn off autocompletion warning messages by
modifying the `SUPPRESS_AUTOCOMPLETE_WARNING` setting as follows:

Example:
    from rcsbapi.config import config

    # Override the default warning suppression flag
    config.SUPPRESS_AUTOCOMPLETE_WARNING = True
"""
import logging

logger = logging.getLogger(__name__)


class Config:
    DATA_API_TIMEOUT: int = 60
    SUPPRESS_AUTOCOMPLETE_WARNING: bool = False

    SEARCH_API_REQUESTS_PER_SECOND: int = 10

    SEQ_API_TIMEOUT: int = 60

    def __setattr__(self, name, value):
        """Verify attribute exists when a user tries to set a configuration parameter, and ensure proper typing.
        Raises an error if user accidentally tries to create a new, unused attribute (e.g., due to a typo or misspelling),
        or sets it to an unexpected type.
        """
        # Verify attribute exists
        if not hasattr(self, name):
            raise AttributeError(f"'{name}' is not a valid attribute of Config class")

        # Enforce consistent typing
        expected_type = self.__annotations__.get(name, None)
        if expected_type and not isinstance(value, expected_type):
            raise TypeError(f"Expected type '{expected_type.__name__}' for attribute '{name}', but got '{type(value).__name__}'")
        super().__setattr__(name, value)


config = Config()
