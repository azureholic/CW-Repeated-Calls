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


def get_application_logger(
    name: str, service_name: str = "repeated-calls-service"
) -> logging.Logger:
    """Create and return an application-specific logger that works with the telemetry setup.

    This function creates a logger that will be captured by OpenTelemetry and sent to
    Azure Monitor when the telemetry is configured.

    Args:
        name: The name for your logger, typically the module name
        service_name: The service name prefix to use (should match telemetry setup)

    Returns:
        A logger instance configured to work with the telemetry setup
    """
    # Create a logger with appropriate naming hierarchy
    logger_name = f"{service_name}.{name}" if name != service_name else service_name
    logger = logging.getLogger(logger_name)

    # Ensure it has at least INFO level set
    if logger.level == logging.NOTSET:
        logger.setLevel(logging.INFO)

    return logger
