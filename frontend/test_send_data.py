import os
from azure.servicebus.aio import ServiceBusClient       # This class is used to interact with queues asynchronously
from azure.servicebus import ServiceBusMessage          # This class ensures that a single message can be sent to the queue
import asyncio
import time
from dotenv import load_dotenv
from repeated_calls.streaming.settings import StreamingSettings

name_of_queue = 'agent_output_messages'
config = StreamingSettings(queue = name_of_queue)


output_dict = {'REPEATED_CALL_AGENT': "Analysis: The current call is about a 'self-driving mower' that isn't working since this morning. The previous call, just one day prior, was about the customer's 'AutoMow 3000' (which is a self-driving mower) that had stopped working. The previous call summary indicates the issue was not resolved immediately and a ticket was opened with a resolution promised by today. The timing is very close (about 1 day apart), and both calls are about the same product and a similar issue (the mower not working). It is highly likely the current call is a follow-up or continuation of the unresolved issue from the previous call. Conclusion: This is a repeated call about the same issue.",
                'CAUSE_AGENT': "Product ID: 101. Analysis: The customer reported that their self-driving mower stopped working on the morning of January 10, 2024. The customer has an active subscription to the AutoMow 3000 (product ID 101). There were no outages or known bugs reported for this product. However, a major software update was rolled out for this product on January 9, 2024, just one day before the issue was reported. It is likely that the recent software update could have caused the malfunction.. Conclusion: The issue is likely related to the recent major software update for the AutoMow 3000, which was rolled out the day before the problem was reported. This suggests that our system may be responsible for the issue.",
                'DRAFTER':"The customer should receive a discount. \
                           - Offer the 20% discount for 6 months. \
                           - Reasoning: The customer, Porter Osborne (Customer ID: 7), has a high Customer Lifetime Value (CLV) and is eligible for the highest available discount (20% for 6 months) for the AutoMow 3000 (Product ID: 101). The issue was likely caused by a recent software update, and providing a significant discount is appropriate to maintain goodwill with a valuable customer. \
                           - The customer reported that their self-driving mower stopped working on the morning of January 10, 2024, possibly due to a software update on January 9, 2024. Please confirm with the customer that the issue began after the update and clarify any additional details about the malfunction. \
                           - Customer ID: 7, Product ID: 101 \
                            Please proceed with offering the 20% discount for 6 months and confirm the issue details with the customer. ",
                'REVIEWER': "APPROVED. The offer is relevant to the customer, as they are experiencing an issue with their AutoMow 3000 (Product ID: 101) that likely resulted from a recent software update. The customer, Porter Osborne (Customer ID: 7), has a high CLV and is eligible for the highest available discount (20% for 6 months). The reasoning behind the offer is clear and logical, aiming to maintain goodwill with a valuable customer. The issue and the need to confirm the timing and details with the customer are clearly stated. Both the customer ID and product ID are included. " 
                                                    }



for i, models_output in enumerate(output_dict):
    
    # time.sleep(5)

    async def send_single_message(sender):                          # Asynchronous function that takes a sender (Instance of the ServiceBusSender class --> from the servicebus.aio SDK) as input
        message = ServiceBusMessage(str(models_output) + ": " + output_dict[models_output])                  # This creates a ServiceBusMessage                             
        await sender.send_messages(message)                         # Sends the message asynchronous using the send_message method
        print('\n \
              ---MESSAGE SENT---')                                       # Await ensures that in the sending time Python can handle other tasks, e.g. sending/receiving messages, web requests, etc).
                                                                    # Async in front of the function allows you to use await inside the function


    # Sending the actual message
    async def run():
        # Create a service bus client using the connection string
        async with ServiceBusClient.from_connection_string(                               # This line creates a new ServiceBusClient called 'servicebus_client' 
            conn_str = config.connection_string,                                                    # Defines the string for which it has to create the ServiceBusClient object
            logging_enable=True) as servicebus_client:                                    # the with part means that the connection will automatically close when you're done    
            sender = servicebus_client.get_queue_sender(queue_name = config.queue)    # Creates an object from the ServiceBusClient that can send messages to the defined queue       
            async with sender:
                # Send one single message
                await send_single_message(sender)

    asyncio.run(run())

