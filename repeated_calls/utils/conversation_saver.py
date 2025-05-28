"""Utility functions for saving chat conversations to files."""

import json
import os
from datetime import datetime

from semantic_kernel.contents.chat_history import ChatHistory

# Define a dictionary of agent names for consistent logging
AGENT_NAMES = {
    "repeated_call": "RepeatedCallDetector",
    "cause": "CauseDeterminer",
    "recommendation": "RecommendationProvider",
}


def setup_logging_directories(base_directory: str = "repeated_calls/conversation_logs") -> str:
    """Create the base logging directories for all agents.

    Args:
        base_directory: Base directory for conversation logs.

    Returns:
        Path to the base directory.
    """
    # Create the base directory
    os.makedirs(base_directory, exist_ok=True)

    # Create directories for each agent
    for agent_name in AGENT_NAMES.values():
        # Directory for all conversations by this agent
        all_convs_dir = os.path.join(base_directory, agent_name, "all_conversations")
        os.makedirs(all_convs_dir, exist_ok=True)

    # Directory for the run log that includes all agents
    run_log_dir = os.path.join(base_directory, "run_logs")
    os.makedirs(run_log_dir, exist_ok=True)

    return base_directory


def format_conversation_with_context(chat_history):
    """Format a conversation adding context to assistant messages.

    The context for assistant messages is the last user message before it.
    """
    messages = []
    last_user_message = ""

    for message in chat_history.messages:
        role = message.role.value.lower()
        if role == "user":
            last_user_message = message.content
            messages.append({"role": role, "content": message.content})
        elif role == "assistant":
            messages.append({"role": role, "content": message.content, "context": last_user_message})
        else:  # system or other roles
            messages.append({"role": role, "content": message.content})

    return {"conversation": {"messages": messages}}


def save_conversation(
    chat_history: ChatHistory,
    agent_name: str,
    row_id: str,
    run_timestamp: str | None = None,
    base_directory: str = "repeated_calls/conversation_logs",
) -> dict:
    """Save a conversation to individual file, conversations file, and run log."""
    if not run_timestamp:
        run_timestamp = get_current_timestamp()

    results = {}

    # Format the conversation with context for assistant messages
    conversation_entry = format_conversation_with_context(chat_history)

    # 1. Save to individual file
    # Create directory structure
    log_dir = os.path.join(base_directory, agent_name, f"row_{row_id}")
    os.makedirs(log_dir, exist_ok=True)

    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = os.path.join(log_dir, f"conversation_{timestamp}.jsonl")

    # Write to individual file
    with open(file_path, "w") as f:
        f.write(json.dumps(conversation_entry))

    results["individual_file"] = file_path

    # 2. Append to conversations file - with naming format "conversations_AgentName.jsonl"
    conversations_dir = os.path.join(base_directory, agent_name, "all_conversations")
    os.makedirs(conversations_dir, exist_ok=True)
    conversations_file = os.path.join(conversations_dir, f"conversations_{agent_name}.jsonl")

    # Use the necessary format for conversations files that adhere to how Azure evaluations expect the data to be structured
    # {"conversation":{"messages":[{"role":"system","content":"message"},{"role":"user","content":"message"},{"role":"assistant","content":"message","context":"user_message"}]}}
    with open(conversations_file, "a") as f:
        f.write(json.dumps(conversation_entry) + "\n")

    results["conversations_file"] = conversations_file

    # 3. Add to run log as formatted JSON (not JSONL)
    run_logs_dir = os.path.join(base_directory, "run_logs")
    os.makedirs(run_logs_dir, exist_ok=True)

    run_log_file = os.path.join(run_logs_dir, f"run_{run_timestamp}.json")

    # Create a more detailed entry for the run log
    run_log_entry = {
        "agent": agent_name,
        "row_id": row_id,
        "timestamp": datetime.now().isoformat(),
        "conversation": conversation_entry["conversation"],
    }

    # Update or create the run log in JSON format
    if os.path.exists(run_log_file):
        # Read existing run log
        with open(run_log_file, "r") as f:
            try:
                run_log = json.load(f)
            except json.JSONDecodeError:
                # If file exists but is empty or invalid, start with new structure
                run_log = {"run_timestamp": run_timestamp, "conversations": []}
    else:
        # Create new run log
        run_log = {"run_timestamp": run_timestamp, "conversations": []}

    # Add the new conversation
    run_log["conversations"].append(run_log_entry)

    # Write the updated run log
    with open(run_log_file, "w") as f:
        json.dump(run_log, f, indent=2)

    results["run_log_file"] = run_log_file

    return results


def get_current_timestamp() -> str:
    """
    Get the current timestamp.

    Returns:
        Current timestamp string formatted as YYYYmmdd_HHMMSS.
    """
    return datetime.now().strftime("%Y%m%d_%H%M%S")
