"""Background process for listening to Azure Service Bus queue."""

import asyncio
import json
import signal
import sys
from typing import Optional

from azure.servicebus.aio import ServiceBusClient, ServiceBusReceiver

from repeated_calls.database.schemas import CallEvent
from repeated_calls.orchestrator.main import run_sequence
from repeated_calls.streaming.settings import StreamingSettings
from repeated_calls.utils.loggers import get_application_logger

# Create a logger
logger = get_application_logger(__name__)

# Global flag to indicate if shutdown was requested
shutdown_requested = False


async def process_message(receiver: ServiceBusReceiver) -> None:
    """Process a single message from the Service Bus queue.
    
    Args:
        receiver: The Service Bus receiver to get messages from.
    """
    try:
        # Get messages from the queue with a 5-second timeout
        messages = await receiver.receive_messages(max_message_count=1, max_wait_time=5)
        
        if not messages:
            return  # No messages to process
        
        for message in messages:
            try:
                # Get the message content - it could be in the message itself
                try:
                    # First attempt: check if the message itself is a string that contains our JSON
                    message_body_str = str(message)
                    # Test if it's valid JSON
                    event_data = json.loads(message_body_str)
                    logger.info(f"Received message (direct JSON): {message_body_str}")
                except json.JSONDecodeError:
                    # Second attempt: message might be an object with a body attribute
                    try:
                        # In some SDK versions this works
                        if hasattr(message, 'message') and message.message:
                            inner_message = message.message
                            if hasattr(inner_message, 'body'):
                                inner_body = inner_message.body
                                if isinstance(inner_body, bytes):
                                    message_body_str = inner_body.decode('utf-8')
                                else:
                                    message_body_str = str(inner_body)
                            else:
                                message_body_str = str(inner_message)
                        # Direct body access
                        elif hasattr(message, 'body'):
                            if isinstance(message.body, bytes):
                                message_body_str = message.body.decode('utf-8')
                            else:
                                message_body_str = str(message.body)
                        else:
                            # Last resort - try to get message content from application properties
                            if hasattr(message, 'application_properties') and message.application_properties:
                                message_body_str = str(message.application_properties)
                            else:
                                # If all else fails, get repr of the message object
                                message_body_str = repr(message)
                        
                        # Try to parse as JSON
                        event_data = json.loads(message_body_str)
                        logger.info(f"Received message (from body): {message_body_str}")
                        
                    except (AttributeError, json.JSONDecodeError) as e:
                        logger.error(f"Failed to parse message: {str(e)}")
                        logger.info(f"Message type: {type(message)}")
                        logger.info(f"Message dir: {dir(message)}")
                        
                        # Try one more approach with newer Azure SDK versions
                        try:
                            # Some versions of the SDK have a get_body method
                            if hasattr(message, 'get_body'):
                                body = message.get_body()
                                if isinstance(body, bytes):
                                    message_body_str = body.decode('utf-8')
                                else:
                                    message_body_str = str(body)
                                event_data = json.loads(message_body_str)
                                logger.info(f"Received message (from get_body): {message_body_str}")
                            else:
                                raise AttributeError("Message does not have get_body method")
                        except Exception as final_err:
                            logger.error(f"All attempts to parse message failed: {str(final_err)}")
                            await receiver.dead_letter_message(
                                message, 
                                reason="Could not parse message format",
                                error_description=f"Failed to extract JSON from message: {str(final_err)}"
                            )
                            continue
                
                try:
                    # Create CallEvent from the message data
                    call_event = CallEvent(
                        id=int(event_data.get("id", -1)),
                        customer_id=int(event_data.get("customer_id", -1)),
                        sdc=event_data.get("sdc", "No description available"),
                        timestamp=event_data.get("timestamp")
                    )
                    
                    # Process the call event
                    logger.info(f"Processing CallEvent with ID: {call_event.id}")
                    
                    # Run the sequence with this call event - no tracing here
                    state = await run_sequence(call_event)
                    logger.info(f"Call processing completed for CallEvent ID: {call_event.id}")
                    
                    # Complete the message (remove from queue)
                    await receiver.complete_message(message)
                    
                except (ValueError, KeyError, TypeError) as e:
                    # Invalid message format
                    logger.error(f"Invalid message format: {str(e)}", exc_info=True)
                    
                    # Dead-letter the message since it has invalid format
                    await receiver.dead_letter_message(
                        message,
                        reason="Invalid message format",
                        error_description=str(e)
                    )
                    
            except Exception as e:
                # General error handling
                logger.error(f"Error processing message: {str(e)}", exc_info=True)
                
                # In case of processing error, abandon the message so it can be retried
                await receiver.abandon_message(message)
    
    except Exception as e:
        logger.error(f"Error receiving messages: {str(e)}", exc_info=True)


async def service_bus_listener() -> None:
    """Background process that continuously listens to the Service Bus queue."""
    # Load Service Bus settings
    settings = StreamingSettings()
    logger.info(f"Starting Service Bus listener for queue: {settings.calls_queue}")
    
    # Create a ServiceBusClient
    async with ServiceBusClient.from_connection_string(
        conn_str=settings.connection_string,
        logging_enable=True
    ) as client:
        # Create a receiver for the calls queue
        async with client.get_queue_receiver(queue_name=settings.calls_queue) as receiver:
            logger.info(f"Connected to queue: {settings.calls_queue}")
            
            # Process messages until shutdown is requested
            while not shutdown_requested:
                try:
                    await process_message(receiver)
                    # Small delay to prevent CPU overuse when queue is empty
                    await asyncio.sleep(0.1)
                except asyncio.CancelledError:
                    logger.info("Listener task was cancelled")
                    break
                except Exception as e:
                    logger.error(f"Unexpected error in listener loop: {str(e)}", exc_info=True)
                    # Add a small delay to prevent rapid error loops
                    await asyncio.sleep(1)
    
    logger.info("Service Bus listener stopped")


def handle_shutdown_signal(sig, frame):
    """Signal handler for graceful shutdown.
    
    Args:
        sig: Signal number
        frame: Current stack frame
    """
    global shutdown_requested
    logger.info(f"Shutdown signal received ({sig}). Stopping...")
    shutdown_requested = True


async def run_listener(stop_event: Optional[asyncio.Event] = None) -> None:
    """Run the Service Bus listener as a background task.
    
    Args:
        stop_event: Optional event to signal when listener should stop
    """
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, handle_shutdown_signal)
    signal.signal(signal.SIGTERM, handle_shutdown_signal)
    
    global shutdown_requested
    try:
        logger.info("Starting Service Bus listener process")
        while not (shutdown_requested or (stop_event and stop_event.is_set())):
            try:
                await service_bus_listener()
            except Exception as e:
                logger.error(f"Service Bus listener error: {str(e)}", exc_info=True)
                # Add a delay before reconnecting to prevent rapid connection attempts
                await asyncio.sleep(5)
    except Exception as e:
        logger.error(f"Error in listener process: {str(e)}", exc_info=True)
    finally:
        logger.info("Service Bus listener process terminated")


if __name__ == "__main__":
    # Run the listener as a standalone process
    try:
        asyncio.run(run_listener())
    except KeyboardInterrupt:
        logger.info("Service Bus listener stopped by keyboard interrupt")
