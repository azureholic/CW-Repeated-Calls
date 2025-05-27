"""GetCustomerData step for the process framework."""

import json
from datetime import datetime, date                 
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.connectors.ai.open_ai import AzureChatPromptExecutionSettings
from semantic_kernel.contents import TextContent
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.functions import KernelArguments, kernel_function
from semantic_kernel.processes.kernel_process import KernelProcessStep, KernelProcessStepContext

from repeated_calls.database.schemas import Customer, HistoricCallEvent, CallEvent
from repeated_calls.orchestrator.entities.state import State
from repeated_calls.orchestrator.entities.structured_output import RepeatedCallResult
from repeated_calls.prompt_engineering.prompts import RepeatCallerPrompt
from repeated_calls.utils.loggers import Logger
from repeated_calls.orchestrator.plugins import (
    customer_plugin,
    operations_plugin,
    McpApiKeyPlugin,
)
from repeated_calls.orchestrator.settings import McpApiKeySettings
from repeated_calls.streaming.settings import StreamingSettings
from frontend import utils as us


config = StreamingSettings(queue = 'agent_output_messages')

logger = Logger()

client = us.get_sb_client(config.connection_string)


class DetermineRepeatedCallStep(KernelProcessStep):
    """Step to retrieve customer data and context for process execution.

    Uses the enhanced database objects with static data loading.
    """

    @kernel_function
    async def repeated_call(
        self,
        state: State,
        context: KernelProcessStepContext,
        kernel: Kernel,
    ) -> None:
        """Process function to retrieve customer data and call events using the enhanced database objects."""
        # Check if incoming_message is already the correct type
        # this code below is to 'fix' semantic_kernel.exceptions.kernel_exceptions.KernelException:
        # The function get_call_event on step GetCustomerDataStep has more than one parameter, so a
        # parameter name must be provided.

        # Retreive the MCP API key by invoking get_mcp_api_key method of McpApiKeyPlugin
        func = kernel.get_function("McpApiKeyPlugin", "get_mcp_api_key")
        mcp_api_key_res = await func.invoke(
            kernel, KernelArguments()
        )
        mcp_api_key = mcp_api_key_res.value

        # Get customer data and historic calls manually
        func = kernel.get_function("CustomerDataPlugin", "get_historic_call_events")
        historic_events_response = await func.invoke(
            kernel, KernelArguments(customer_id=state.call_event.customer_id, mcp_api_key=mcp_api_key)
        )

        # --- 1⃣ history ---------------------------------------------------
        he_raw = historic_events_response.value

        # Check if MCP API key is invalid or missing
        if (isinstance(he_raw, list) and he_raw and isinstance(he_raw[0], TextContent)
            and "Invalid or missing MCP API Key" in he_raw[0].text):
            logger.error(f"Historic events error: {he_raw[0].text}")
            await context.emit_event("Exit", data={"error": he_raw[0].text})
            return

        # unwrap TextContent / JSON-string once
        if isinstance(he_raw, TextContent):
            he_raw = he_raw.text
        if isinstance(he_raw, str):
            he_raw = json.loads(he_raw)

        # he_raw is either the list of events or the FastMCP wrapper
        historic_events_list = (
            he_raw if isinstance(he_raw, list) else he_raw.get("events", [])
        )

        normalized_events: list[dict] = []
        for evt in historic_events_list:
            # unwrap nested TextContent / JSON
            if isinstance(evt, TextContent):
                evt = evt.text
            if isinstance(evt, str):
                evt = json.loads(evt)

            # << FIX — skip wrapper dicts that contain their own "events" key >>
            if isinstance(evt, dict) and "events" in evt:
                normalized_events.extend(evt["events"])
                continue

            if isinstance(evt, dict):
                normalized_events.append(evt)
            else:
                logger.warning("Skipping non-dict historic event: %s", type(evt))

        historic_events = [HistoricCallEvent(**e) for e in normalized_events]

        # --- 2⃣ customer ---------------------------------------------------
        func = kernel.get_function("CustomerDataPlugin", "get_customer_by_id")
        cust_resp = await func.invoke(
            kernel, KernelArguments(customer_id=state.call_event.customer_id, mcp_api_key=mcp_api_key)
        )
        cust_raw = cust_resp.value

        # Check if MCP API key is invalid or missing
        if (isinstance(cust_raw, list) and cust_raw and isinstance(cust_raw[0], TextContent)
            and "Invalid or missing MCP API Key" in cust_raw[0].text):
            logger.error(f"Customer data error: {cust_raw[0].text}")
            await context.emit_event("Exit", data={"error": cust_raw[0].text})
            return

        if isinstance(cust_raw, TextContent):
            cust_raw = cust_raw.text
        if isinstance(cust_raw, str):
            cust_raw = json.loads(cust_raw)

        customer_payload = (
            cust_raw.get("customer") if isinstance(cust_raw, dict) else None
        )
        customer_obj = (
            Customer(**customer_payload)
            if customer_payload
            else Customer(
                id=state.call_event.customer_id,
                name="Unknown",
                clv="Unknown",
                relation_start_date=date.today(),   # exact date → passes pydantic validation
            )
        )

        # Update state
        state.update(customer_obj, historic_events)

        # Classify whether the call is a repeated call with an LLM
        chat_service = kernel.get_service(type=ChatCompletionClientBase)
        chat_settings = AzureChatPromptExecutionSettings(response_format=RepeatedCallResult, temperature=0.0)

        # Prepare the chat interaction
        chat_history = ChatHistory()
        prompts = RepeatCallerPrompt(state)

        # logger.debug(f"System prompt:\n{prompts.get_system_prompt()}")
        # logger.debug(f"User prompt:\n{prompts.get_user_prompt()}")

        chat_history.add_system_message(prompts.get_system_prompt())
        chat_history.add_user_message(prompts.get_user_prompt())

        response = await chat_service.get_chat_message_content(
            chat_history=chat_history,
            settings=chat_settings,
        )
        chat_history.add_assistant_message(response.content)

        res = RepeatedCallResult(**json.loads(response.content))
        msg_1 = f">> REPEATED CALL AGENT - \n Analysis: {res.analysis} Conclusion: {res.conclusion}"
        await us._send_async(msg_1, client, config.queue)
        logger.debug(msg_1)
        state.update(res)

        # Log the decision and reasoning
        msg_2 = "=== REPEATED CALL DECISION ==="
        msg_3 = f"Is repeated call: {state.repeated_call_result.is_repeated_call}"
        msg_4 = f"Analysis: {state.repeated_call_result.analysis}"
        msg_5 = f"Conclusion: {state.repeated_call_result.conclusion}"
        logger.debug(msg_2)
        logger.debug(msg_3)
        logger.debug(msg_4)
        logger.debug(msg_5)

        # Before emitting event
        msg_6 = f"Emitting event: {'IsRepeatedCall' if state.repeated_call_result.is_repeated_call else 'IsNotRepeatedCall'}"
        logger.debug(msg_6)

        # Sending message to the servicebus
        messages = [msg_2, msg_3, msg_4, msg_5, msg_6]
        total_message = us.create_one_message(messages)
        await us._send_async(total_message, client, config.queue)

        # Emit event to continue process flow
        if res.is_repeated_call:
            await context.emit_event("IsRepeatedCall", data=state)
        else:
            await context.emit_event("IsNotRepeatedCall", data=state)
