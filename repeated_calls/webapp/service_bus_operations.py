"""
Service Bus Operations Module

This module provides functionality to interact with Azure Service Bus for sending and receiving messages.
Supports the complete flow for the Repeated Calls application.
"""
import json
import asyncio
import os
import logging
from typing import List, Dict, Any, Optional, Union
from azure.servicebus.aio import ServiceBusClient
from azure.servicebus import ServiceBusMessage
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv(dotenv_path='connection-string-servicebus.env')

# Try to get connection string from environment variable first, then fallback to hardcoded (for demo)
CONNECTION_STR = os.getenv('AZURE_SERVICEBUS_CONNECTION_STRING')

# Queue names
QUEUE_INPUT = 'customercalls'
QUEUE_RESULTS = 'callresults'

class ServiceBusOperations:
    """Class that handles Azure Service Bus operations with retry logic and proper error handling."""
    
    @staticmethod
    async def send_message(message_content: Union[str, Dict[str, Any]], queue_name: str = QUEUE_INPUT) -> bool:
        """
        Send a message to Azure Service Bus queue with retry logic.
        
        Args:
            message_content: Content to send to Service Bus. If dict, it will be converted to JSON string.
            queue_name: Name of the queue to send the message to. Defaults to input queue.
        
        Returns:
            True if message was sent successfully, False otherwise.
        """
        if not CONNECTION_STR:
            logger.error("Service Bus connection string not found in environment variables")
            return False
            
        # Convert dict to JSON string if needed
        if isinstance(message_content, dict):
            try:
                message_content = json.dumps(message_content, default=str)
            except (TypeError, ValueError) as e:
                logger.error(f"Error serializing message content to JSON: {str(e)}")
                return False
        
        # Retry logic
        max_retries = 3
        retry_delay = 1.0
        
        for attempt in range(max_retries):
            try:
                # Create a Service Bus client
                async with ServiceBusClient.from_connection_string(
                    conn_str=CONNECTION_STR,
                    logging_enable=True
                ) as servicebus_client:
                    # Create a sender for the queue
                    sender = servicebus_client.get_queue_sender(queue_name=queue_name)
                    
                    async with sender:
                        # Create and send the message
                        message = ServiceBusMessage(message_content)
                        await sender.send_messages(message)
                        logger.info(f"Message sent successfully to queue: {queue_name}")
                        return True
                        
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed to send message to Service Bus queue {queue_name}: {str(e)}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    logger.error(f"Failed to send message after {max_retries} attempts: {str(e)}")
                    
        return False
    
    @staticmethod
    async def receive_messages(
        queue_name: str = QUEUE_INPUT, 
        max_messages: int = 100, 
        wait_time: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Receive messages from Azure Service Bus queue with proper message completion.
        
        Args:
            queue_name: Name of the queue to receive messages from. Defaults to input queue.
            max_messages: Maximum number of messages to receive.
            wait_time: Maximum time to wait for messages in seconds.
            
        Returns:
            List of received messages as dictionaries or empty list if none received.
        """
        if not CONNECTION_STR:
            logger.error("Service Bus connection string not found in environment variables")
            return []
            
        received_msgs = []
        
        try:
            # Create a Service Bus client
            async with ServiceBusClient.from_connection_string(
                conn_str=CONNECTION_STR,
                logging_enable=True
            ) as servicebus_client:
                # Create a receiver for the queue
                receiver = servicebus_client.get_queue_receiver(queue_name=queue_name)
                
                async with receiver:
                    # Receive messages from the queue
                    messages = await receiver.receive_messages(
                        max_wait_time=wait_time, 
                        max_message_count=max_messages
                    )
                    
                    for message in messages:
                        try:
                            # Parse message content
                            message_body = str(message)
                            
                            # Try to parse as JSON, fallback to string
                            try:
                                parsed_content = json.loads(message_body)
                            except json.JSONDecodeError:
                                parsed_content = message_body
                            
                            received_msgs.append(parsed_content)
                            
                            # Complete the message to remove it from the queue
                            await receiver.complete_message(message)
                            logger.info(f"Message received and completed from queue: {queue_name}")
                            
                        except Exception as e:
                            logger.error(f"Error processing message: {str(e)}")
                            # Abandon the message so it can be retried
                            try:
                                await receiver.abandon_message(message)
                            except:
                                pass
                    
                    if not received_msgs:
                        logger.info(f"No messages found in queue: {queue_name}")
                    else:
                        logger.info(f"Received {len(received_msgs)} messages from queue: {queue_name}")
                        
        except Exception as e:
            logger.error(f"Error connecting to Service Bus queue {queue_name}: {str(e)}")
        
        return received_msgs

    @staticmethod
    async def send_result(result_data: Dict[str, Any]) -> bool:
        """
        Send a result message to the results queue.
        
        Args:
            result_data: Result data to send.
        
        Returns:
            True if message was sent successfully, False otherwise.
        """
        logger.info("Sending result to results queue")
        return await ServiceBusOperations.send_message(result_data, QUEUE_RESULTS)
    
    @staticmethod
    async def receive_results(max_messages: int = 100, wait_time: int = 5) -> List[Dict[str, Any]]:
        """
        Receive result messages from the results queue.
        
        Args:
            max_messages: Maximum number of messages to receive.
            wait_time: Maximum time to wait for messages in seconds.
            
        Returns:
            List of received messages or empty list if none received.
        """
        logger.info("Receiving results from results queue")
        return await ServiceBusOperations.receive_messages(QUEUE_RESULTS, max_messages, wait_time)

    @staticmethod
    async def peek_messages(queue_name: str = QUEUE_INPUT, max_messages: int = 10) -> List[Dict[str, Any]]:
        """
        Peek at messages in the queue without removing them.
        
        Args:
            queue_name: Name of the queue to peek into.
            max_messages: Maximum number of messages to peek.
            
        Returns:
            List of peeked messages or empty list if none found.
        """
        if not CONNECTION_STR:
            logger.error("Service Bus connection string not found in environment variables")
            return []
            
        peeked_msgs = []
        
        try:
            async with ServiceBusClient.from_connection_string(
                conn_str=CONNECTION_STR,
                logging_enable=True
            ) as servicebus_client:
                receiver = servicebus_client.get_queue_receiver(queue_name=queue_name)
                
                async with receiver:
                    messages = await receiver.peek_messages(max_message_count=max_messages)
                    
                    for message in messages:
                        try:
                            message_body = str(message)
                            try:
                                parsed_content = json.loads(message_body)
                            except json.JSONDecodeError:
                                parsed_content = message_body
                            
                            peeked_msgs.append(parsed_content)
                            
                        except Exception as e:
                            logger.error(f"Error processing peeked message: {str(e)}")
                    
                    logger.info(f"Peeked at {len(peeked_msgs)} messages in queue: {queue_name}")
                        
        except Exception as e:
            logger.error(f"Error peeking at Service Bus queue {queue_name}: {str(e)}")
        
        return peeked_msgs

    @staticmethod
    async def get_queue_properties(queue_name: str = QUEUE_INPUT) -> Optional[Dict[str, Any]]:
        """
        Get queue properties like message count, dead letter count, etc.
        
        Args:
            queue_name: Name of the queue to get properties for.
            
        Returns:
            Dictionary with queue properties or None if error.
        """
        if not CONNECTION_STR:
            logger.error("Service Bus connection string not found in environment variables")
            return None
            
        try:
            async with ServiceBusClient.from_connection_string(
                conn_str=CONNECTION_STR,
                logging_enable=True
            ) as servicebus_client:
                properties = await servicebus_client.get_queue(queue_name)
                
                return {
                    "name": properties.name,
                    "active_message_count": properties.active_message_count,
                    "dead_letter_message_count": properties.dead_letter_message_count,
                    "scheduled_message_count": properties.scheduled_message_count,
                    "transfer_dead_letter_message_count": properties.transfer_dead_letter_message_count,
                    "total_message_count": (
                        properties.active_message_count + 
                        properties.dead_letter_message_count + 
                        properties.scheduled_message_count + 
                        properties.transfer_dead_letter_message_count
                    )
                }
                
        except Exception as e:
            logger.error(f"Error getting queue properties for {queue_name}: {str(e)}")
            return None


# Example usage functions
async def send_example():
    """Example function showing how to send a message."""
    message = {
        "customer_id": "12345",
        "call_reason": "Product inquiry",
        "timestamp": "2024-01-01T10:00:00"
    }
    success = await ServiceBusOperations.send_message(message)
    print(f"Message sent successfully: {success}")


async def receive_example():
    """Example function showing how to receive messages."""
    messages = await ServiceBusOperations.receive_messages()
    if messages:
        print(f"Received {len(messages)} messages:")
        for i, msg in enumerate(messages, 1):
            print(f"Message {i}: {msg}")
    else:
        print("No messages received")


async def send_and_receive_example():
    """Example showing the complete flow."""
    print("=== Sending a test message ===")
    await send_example()
    
    print("\n=== Receiving messages ===")
    await receive_example()
    
    print("\n=== Getting queue properties ===")
    props = await ServiceBusOperations.get_queue_properties()
    if props:
        print(f"Queue properties: {props}")


# Main function for testing
async def main():
    """Main function to demonstrate sending and receiving messages."""
    await send_and_receive_example()


# Entry point for script execution
if __name__ == "__main__":
    asyncio.run(main())
