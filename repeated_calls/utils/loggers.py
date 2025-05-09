import logging
import logging.config
from importlib import resources

import yaml


class Logger:
    """A singleton logger class to retrieve and/or create logger instances.

    Logger instances are configured in the `.logging_config.yaml` file located in the `utils`
    package.
    """

    _loggers = {}
    _config = None

    def __new__(cls, name="default") -> logging.Logger:
        """Creates a new logger instance if it does not exist yet.

        Args:
            name (str): The name of the logger.

        Returns:
            logging.Logger: The logger instance with name `name`.
        """
        if name not in cls._loggers:
            if not cls._config:
                with open(
                    resources.files("repeated_calls.utils") / ".logging_config.yaml", "r"
                ) as f:
                    cls._config = yaml.safe_load(f)

                logging.config.dictConfig(cls._config)

            cls._loggers[name] = logging.getLogger(name)

        return cls._loggers[name]
