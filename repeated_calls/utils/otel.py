"""OpenTelemetry configuration for Azure Monitor integration."""

import logging
import os
from typing import Optional

from azure.monitor.opentelemetry.exporter import AzureMonitorLogExporter, AzureMonitorTraceExporter
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# For logging
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor

# for OpenAI
from opentelemetry.instrumentation.openai_v2 import OpenAIInstrumentor


# Importing from local utils
from repeated_calls.utils.loggers import get_application_logger


class TelemetrySetup:
    """Configure OpenTelemetry with Azure Monitor."""

    def __init__(self, connection_string: str, service_name: str = "repeated-calls-service"):
        """Initialize telemetry setup.
        
        Args:
            connection_string: Azure Monitor connection string
            service_name: Name of your service
        """
        self.connection_string = connection_string
        self.service_name = service_name
        self.resource = Resource.create({"service.name": service_name})
        self._setup_completed = False
        os.environ["OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT"] = "true"
        os.environ["AZURE_TRACING_GEN_AI_CONTENT_RECORDING_ENABLED"]= "true"
        os.environ["SEMANTICKERNEL_EXPERIMENTAL_GENAI_ENABLE_OTEL_DIAGNOSTICS_SENSITIVE"] = "true"
        OpenAIInstrumentor().instrument()
        
    def setup(self):
        """Configure and initialize all telemetry components."""
        if self._setup_completed:
            return
            
        # Set up tracing
        self._setup_tracing()
        
        # Set up logging
        self._setup_logging()
        
        self._setup_completed = True
        
    def _setup_tracing(self):
        """Configure trace export to Azure Monitor."""
        tracer_provider = TracerProvider(resource=self.resource)
        trace.set_tracer_provider(tracer_provider)
        
        
        # Create Azure Monitor span exporter
        azure_exporter = AzureMonitorTraceExporter(connection_string=self.connection_string)
        span_processor = BatchSpanProcessor(azure_exporter)
        tracer_provider.add_span_processor(span_processor)
    
    def _setup_logging(self):
        """Configure logging export to Azure Monitor."""
        # Create Azure Monitor log exporter
        azure_log_exporter = AzureMonitorLogExporter(connection_string=self.connection_string)
        
        # Create logger provider with the Azure Monitor exporter
        logger_provider = LoggerProvider(resource=self.resource)
        logger_provider.add_log_record_processor(
            BatchLogRecordProcessor(azure_log_exporter)
        )
        
        # Create a logging handler for OpenTelemetry
        handler = LoggingHandler(level=logging.INFO, logger_provider=logger_provider)
        
        # Set log levels for OpenTelemetry internal loggers to reduce noise
        logging.getLogger('opentelemetry').setLevel(logging.WARNING)
        logging.getLogger('azure.monitor').setLevel(logging.WARNING)
        
        # Configure Python's logging module to use this handler, but only for your app's loggers
        app_logger = logging.getLogger(self.service_name)
        app_logger.setLevel(logging.INFO)
        app_logger.addHandler(handler)
        
        # Optional: If you still want a root logger handler but with controlled verbosity
        # logging.getLogger().setLevel(logging.WARNING)


def configure_telemetry(connection_string: Optional[str] = None, service_name: str = "repeated-calls-service"):
    """Helper function to configure telemetry in one call.
    
    Args:
        connection_string: Azure Monitor connection string. If None, looks for 
                          APPLICATIONINSIGHTS_CONNECTION_STRING environment variable
        service_name: Name of your service
    """
    import os
    
    if connection_string is None:
        connection_string = os.environ.get("APPLICATIONINSIGHTS_CONNECTION_STRING")
        if not connection_string:
            raise ValueError(
                "No connection string provided. Set APPLICATIONINSIGHTS_CONNECTION_STRING "
                "environment variable or pass connection_string parameter"
            )
    
    telemetry = TelemetrySetup(connection_string, service_name)
    telemetry.setup()
    return telemetry


# Example usage of the logger:
# from repeated_calls.utils.loggers import get_application_logger
# logger = get_application_logger(__name__)
# logger.info("This will be sent to Azure Monitor")