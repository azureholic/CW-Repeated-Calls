"""GetCustomerData step for the process framework."""

import json
from datetime import date

from semantic_kernel import Kernel
from semantic_kernel.contents import TextContent
from semantic_kernel.functions import KernelArguments, kernel_function
from semantic_kernel.processes.kernel_process import KernelProcessStep, KernelProcessStepContext

from repeated_calls.database.schemas import Customer, HistoricCallEvent
from repeated_calls.orchestrator.agents.repeated_call_agent import get_agent
from repeated_calls.orchestrator.entities.state import State
from repeated_calls.orchestrator.entities.structured_output import RepeatedCallResult
from repeated_calls.prompt_engineering.prompts import RepeatCallerPrompt
from repeated_calls.utils.loggers import Logger

logger = Logger()


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
        mcp_api_key_res = await func.invoke(kernel, KernelArguments())
        mcp_api_key = mcp_api_key_res.value

        # Get customer data and historic calls manually
        func = kernel.get_function("CustomerDataPlugin", "get_historic_call_events")
        historic_events_response = await func.invoke(
            kernel,
            KernelArguments(customer_id=state.call_event.customer_id, mcp_api_key=mcp_api_key),
        )

        # --- 1⃣ history ---------------------------------------------------
        he_raw = historic_events_response.value

        # Check if MCP API key is invalid or missing
        if (
            isinstance(he_raw, list)
            and he_raw
            and isinstance(he_raw[0], TextContent)
            and "Invalid or missing MCP API Key" in he_raw[0].text
        ):
            logger.error(f"Historic events error: {he_raw[0].text}")
            await context.emit_event("Exit", data={"error": he_raw[0].text})
            return

        # unwrap TextContent / JSON-string once
        if isinstance(he_raw, TextContent):
            he_raw = he_raw.text
        if isinstance(he_raw, str):
            he_raw = json.loads(he_raw)

        # he_raw is either the list of events or the FastMCP wrapper
        historic_events_list = he_raw if isinstance(he_raw, list) else he_raw.get("events", [])

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
            kernel,
            KernelArguments(customer_id=state.call_event.customer_id, mcp_api_key=mcp_api_key),
        )
        cust_raw = cust_resp.value

        # Check if MCP API key is invalid or missing
        if (
            isinstance(cust_raw, list)
            and cust_raw
            and isinstance(cust_raw[0], TextContent)
            and "Invalid or missing MCP API Key" in cust_raw[0].text
        ):
            logger.error(f"Customer data error: {cust_raw[0].text}")
            await context.emit_event("Exit", data={"error": cust_raw[0].text})
            return

        if isinstance(cust_raw, list):
            cust_raw = cust_raw[0].text
            cust_raw = json.loads(cust_raw)
        elif isinstance(cust_raw, str):
            cust_raw = json.loads(cust_raw)

        customer_payload = cust_raw.get("customer") if isinstance(cust_raw, dict) else None
        customer_obj = (
            Customer(**customer_payload)
            if customer_payload
            else Customer(
                id=state.call_event.customer_id,
                name="Unknown",
                clv="Unknown",
                relation_start_date=date.today(),  # exact date → passes pydantic validation
            )
        )
        logger.debug(f"Customer Info: ID={customer_obj.id}, Name={customer_obj.name}, CLV={customer_obj.clv}")
        # Update state
        state.update(customer_obj, historic_events)

        prompts = RepeatCallerPrompt(state)

        agent = get_agent(kernel=kernel, instructions=prompts.get_prompt("system"))

        response = await agent.get_response(
            messages=prompts.get_prompt("user"),
        )

        # Parse the response and update the state
        res = RepeatedCallResult(**json.loads(response.content.content))
        logger.debug(f">> REPEATED CALL AGENT - Analysis: {res.analysis} Conclusion: {res.conclusion}")
        state.update(res)

        # Log the decision and reasoning
        logger.debug("=== REPEATED CALL DECISION ===")
        logger.debug(f"Is repeated call: {state.repeated_call_result.is_repeated_call}")
        logger.debug(f"Analysis: {state.repeated_call_result.analysis}")
        logger.debug(f"Conclusion: {state.repeated_call_result.conclusion}")

        # Before emitting event
        logger.debug(
            f"Emitting event: {'IsRepeatedCall' if state.repeated_call_result.is_repeated_call else 'IsNotRepeatedCall'}"
        )
        logger.debug(f"Repeated call response: {response.content}")

        # Emit event to continue process flow
        if res.is_repeated_call:
            await context.emit_event("IsRepeatedCall", data=state)
        else:
            await context.emit_event("IsNotRepeatedCall", data=state)
