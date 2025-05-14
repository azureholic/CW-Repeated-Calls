#!/usr/bin/env python
# Copyright (c) Microsoft. All rights reserved.

import os
import json
from datetime import datetime
from semantic_kernel.agents import AgentGroupChat
from semantic_kernel.functions.kernel_arguments import KernelArguments

from src.models import (
    FinalRecommendation,
    CompensationReview,
    ConversationHistory,
)
from src.agents import (
    create_repeat_call_detector,
    create_fault_analyzer,
    create_compensation_recommender,
    create_compensation_reviewer,
    create_recommendation_publisher,
    create_group_chat_recommender,
    ApprovalTerminationStrategy,
)

# Directory paths
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "output")


def create_timestamped_output_dir(call_id):
    """Create a timestamped output directory for results.

    Args:
        call_id: The ID of the call being processed

    Returns:
        str: Path to the timestamped output directory
    """
    # Generate a timestamp for the directory name in a format that sorts well
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = os.path.join(OUTPUT_DIR, f"{timestamp_str}_{call_id}")

    # Create the directory
    os.makedirs(output_dir, exist_ok=True)

    return output_dir


async def process_call(calls, customer_data, disruption_data, result_dir):
    """Process a call with the agent workflow.

    Args:
        calls: List of call data
        customer_data: List of customer data
        disruption_data: List of disruption data
        result_dir: Directory to save results

    Returns:
        FinalRecommendation: The final recommendation
    """
    # Extract the current call to process
    current_call = calls[-1]  # Assuming the most recent call is the last in the list
    customer_id = current_call["customer_id"]

    # Find customer information
    customer_info = next((c for c in customer_data if c["customer_id"] == customer_id), None)
    if not customer_info:
        print(f"Customer {customer_id} not found in customer data.")
        return

    # 1. Process with the repeat call detection agent
    repeat_agent = create_repeat_call_detector()
    call_history = json.dumps([c for c in calls if c["customer_id"] == customer_id])
    repeat_input = f"Current call: {json.dumps(current_call)}\nCall history: {call_history}"

    repeat_response = await repeat_agent.get_response(messages=repeat_input)
    repeat_analysis = json.loads(repeat_response.message.content)
    print(f"Repeat Call Analysis: {json.dumps(repeat_analysis, indent=2)}")

    # Prepare variables for different outcomes
    fault_analysis = None
    compensation_recommendation = None
    compensation_review = None
    call_agent_summary = None
    conversation_history = ConversationHistory(messages=[])

    # If not a repeat call, create a call agent summary and save the output
    if not repeat_analysis["is_repeat_call"]:
        print("Not a repeat call. No further action needed.")

        # Create the call agent summary
        publisher_agent = create_recommendation_publisher()
        publisher_input = f"""
        Current call: {json.dumps(current_call)}
        Customer information: {json.dumps(customer_info)}
        Repeat call analysis: {json.dumps(repeat_analysis)}

        This is NOT a repeat call, so no compensation is required. Please provide appropriate guidance to the call agent.
        """

        publisher_response = await publisher_agent.get_response(messages=publisher_input)
        call_agent_summary = json.loads(publisher_response.message.content)
        print(f"Call Agent Summary: {json.dumps(call_agent_summary, indent=2)}")

    # If it is a repeat call, continue with the regular flow
    else:
        # 2. Process with fault determination agent
        fault_agent = create_fault_analyzer()
        fault_input = f"""
        Current call: {json.dumps(current_call)}
        Call history: {call_history}
        Customer information: {json.dumps(customer_info)}
        Operational disruptions: {json.dumps(disruption_data)}
        Repeat call analysis: {json.dumps(repeat_analysis)}
        """

        fault_response = await fault_agent.get_response(messages=fault_input)
        fault_analysis = json.loads(fault_response.message.content)
        print(f"Fault Analysis: {json.dumps(fault_analysis, indent=2)}")

        # If not our fault, create a call agent summary and save the output
        if not fault_analysis["is_our_fault"]:
            print("Issue is not our fault. No compensation needed.")

            # Create the call agent summary
            publisher_agent = create_recommendation_publisher()
            publisher_input = f"""
            Current call: {json.dumps(current_call)}
            Customer information: {json.dumps(customer_info)}
            Repeat call analysis: {json.dumps(repeat_analysis)}
            Fault analysis: {json.dumps(fault_analysis)}

            This is a repeat call, but NOT our fault, so no compensation is required.
            Please provide appropriate guidance to the call agent on how to handle this diplomatically.
            """

            publisher_response = await publisher_agent.get_response(messages=publisher_input)
            call_agent_summary = json.loads(publisher_response.message.content)
            print(f"Call Agent Summary: {json.dumps(call_agent_summary, indent=2)}")

        # If it is our fault, continue with the regular flow
        else:
            # 3. Process with compensation recommendation agent
            recommend_agent = create_compensation_recommender()
            recommend_input = f"""
            Current call: {json.dumps(current_call)}
            Call history: {call_history}
            Customer information: {json.dumps(customer_info)}
            Repeat call analysis: {json.dumps(repeat_analysis)}
            Fault analysis: {json.dumps(fault_analysis)}
            """

            recommend_response = await recommend_agent.get_response(messages=recommend_input)
            compensation_recommendation = json.loads(recommend_response.message.content)
            print(
                f"Compensation Recommendation: {json.dumps(compensation_recommendation, indent=2)}"
            )

            # 4. Process with compensation review
            reviewer_agent = create_compensation_reviewer()
            recommender_agent = create_group_chat_recommender()

            # 5. Create a group chat between the recommender and reviewer
            group_chat = AgentGroupChat(
                agents=[recommender_agent, reviewer_agent],
                termination_strategy=ApprovalTerminationStrategy(
                    agents=[reviewer_agent],
                    maximum_iterations=5,
                ),
            )

            # Start the group chat with the recommendation
            group_chat_input = f"""
            CONTEXT:
            Current call: {json.dumps(current_call)}
            Customer information: {json.dumps(customer_info)}
            Repeat call analysis: {json.dumps(repeat_analysis)}
            Fault analysis: {json.dumps(fault_analysis)}

            INITIAL RECOMMENDATION:
            {json.dumps(compensation_recommendation, indent=2)}

            Please review this compensation recommendation.
            """

            await group_chat.add_chat_message(message=group_chat_input)

            # Collect messages from the group chat
            chat_messages = []
            conversation_messages = []
            async for message in group_chat.invoke():
                message_text = f"# {message.name}: {message.content}"
                chat_messages.append(message_text)
                conversation_messages.append(
                    {
                        "name": message.name,
                        "content": message.content,
                        "timestamp": datetime.now().isoformat(),
                    }
                )
                print(message_text)

            # Store conversation history
            conversation_history = ConversationHistory(messages=conversation_messages)

            # Extract the final review decision from the last reviewer message
            final_review_content = None
            for message in reversed(chat_messages):
                if "CompensationReviewer" in message:
                    final_review_content = message.split(": ", 1)[1]
                    break

            if final_review_content:
                compensation_review = json.loads(final_review_content)
            else:
                # Default review if extraction fails
                compensation_review = CompensationReview(
                    approved=False,
                    comments="Review process did not complete successfully.",
                )

            # 6. Create the recommendation publisher for call agent consumption
            publisher_agent = create_recommendation_publisher()

            # Create input for the publisher
            final_compensation_type = compensation_review.get(
                "adjusted_type"
            ) or compensation_recommendation.get("recommended_compensation_type")
            final_compensation_amount = (
                compensation_review.get("adjusted_amount")
                if compensation_review.get("adjusted_amount") is not None
                else compensation_recommendation.get("amount")
            )

            publisher_input = f"""
            Current call: {json.dumps(current_call)}
            Customer information: {json.dumps(customer_info)}
            Repeat call analysis: {json.dumps(repeat_analysis)}
            Fault analysis: {json.dumps(fault_analysis)}
            Compensation recommendation: {json.dumps(compensation_recommendation)}
            Compensation review: {json.dumps(compensation_review)}

            The final approved compensation is: {final_compensation_type} in the amount of {final_compensation_amount}.
            """

            # Get response from publisher agent
            publisher_response = await publisher_agent.get_response(messages=publisher_input)
            call_agent_summary = json.loads(publisher_response.message.content)
            print(f"Call Agent Summary: {json.dumps(call_agent_summary, indent=2)}")

    # 7. Create the final recommendation with all available data
    final_recommendation = FinalRecommendation(
        customer_id=customer_id,
        call_id=current_call["call_id"],
        timestamp=datetime.now().isoformat(),
        repeat_call_analysis=repeat_analysis,
        fault_analysis=fault_analysis,
        compensation_recommendation=compensation_recommendation,
        compensation_review=compensation_review,
        call_agent_summary=call_agent_summary,
        conversation_history=conversation_history,
    )

    # Save the recommendation to the result directory
    output_path = os.path.join(result_dir, "recommendation.json")
    with open(output_path, "w") as file:
        file.write(final_recommendation.model_dump_json(indent=2, exclude_none=True))

    print(f"Final recommendation saved to {output_path}")
    return final_recommendation


async def process_specific_call(call_id, calls, customer, disruptions):
    """Process a specific call with provided data.

    Args:
        call_id: ID of the call to process
        calls: List of call data
        customer: Customer data
        disruptions: List of disruption data

    Returns:
        FinalRecommendation: The final recommendation
    """
    print(f"Processing call {call_id}...")

    # Create a timestamped directory for results
    result_dir = create_timestamped_output_dir(call_id)

    # Save context data to the result directory
    context_dir = os.path.join(result_dir, "context")
    os.makedirs(context_dir, exist_ok=True)

    # Save context files
    with open(os.path.join(context_dir, "calls.json"), "w") as file:
        json.dump(calls, file, indent=2)

    with open(os.path.join(context_dir, "customer.json"), "w") as file:
        json.dump(customer, file, indent=2)

    with open(os.path.join(context_dir, "disruptions.json"), "w") as file:
        json.dump(disruptions, file, indent=2)

    # Process the call with our workflow
    result = await process_call(calls, [customer], disruptions, result_dir)

    # Print a summary of the recommendation
    if result:
        print(f"Call processed successfully.")

        repeat_analysis = result.repeat_call_analysis
        fault_analysis = result.fault_analysis

        print("\nSummary:")
        print(f"Repeat Call: {repeat_analysis.is_repeat_call}")
        print(f"Reasoning: {repeat_analysis.reasoning}")

        if repeat_analysis.is_repeat_call:
            print(f"Issue: {repeat_analysis.issue_summary}")
            print(f"Days since first call: {repeat_analysis.days_since_first_call}")
            print(f"Our Fault: {fault_analysis.is_our_fault if fault_analysis else 'N/A'}")

            if fault_analysis and fault_analysis.is_our_fault:
                print(f"Fault Reason: {fault_analysis.fault_reason}")
                print(f"Reasoning: {fault_analysis.reasoning}")
                print(f"Recommended Action: {fault_analysis.recommended_action}")

                # Print compensation details if a recommendation was made
                if result.compensation_recommendation:
                    comp = result.compensation_recommendation
                    review = result.compensation_review
                    summary = result.call_agent_summary

                    print("\nCompensation Recommendation:")
                    print(f"Type: {comp.recommended_compensation_type}")
                    print(f"Amount: {comp.amount}")
                    if comp.duration:
                        print(f"Duration: {comp.duration}")

                    print("\nReview Decision:")
                    print(f"Approved: {review.approved}")
                    if review.adjusted_amount:
                        print(f"Adjusted Amount: {review.adjusted_amount}")
                    if review.adjusted_type:
                        print(f"Adjusted Type: {review.adjusted_type}")
                    print(f"Comments: {review.comments}")
            elif fault_analysis:
                print(f"Reasoning: {fault_analysis.reasoning}")

        # Always print the call agent summary if it exists
        if result.call_agent_summary:
            summary = result.call_agent_summary
            print("\nCall Agent Summary:")
            print(f"Quick Recommendation: {summary.one_sentence_recommendation}")
            print(f"Compensation Details: {summary.compensation_details}")
            print(f"Technical Resolution: {summary.technical_resolution}")

            print("\nTalking Points:")
            for i, point in enumerate(summary.talking_points, 1):
                print(f"{i}. {point}")

            print(f"\nNext Steps: {summary.next_steps}")
    else:
        print(f"No recommendation generated for this call.")

    print(f"Results saved to: {result_dir}")
    return result
