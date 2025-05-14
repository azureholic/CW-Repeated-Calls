# Repeated Call Handling MVP Sample

A tool for analyzing call events to identify repeated calls, determine fault, and recommend appropriate compensation.

## Table of Contents

- [Agent Workflow](#agent-workflow)
  - [Workflow Overview](#workflow-overview)
  - [Agent Roles](#agent-roles)
  - [Group Chat Process](#group-chat-process)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Usage](#usage)
- [Example Calls](#example-calls)
- [Example Responses](#example-responses)

## Agent Workflow

### Workflow Overview

Call → Repeat Detection → (If repeat) Fault Analysis → (If our fault) Compensation Recommendation → Review → Call Agent Summary

The system processes each call through a sequential pipeline of specialized agents. First determining if it's a repeat call, then analyzing fault for repeat calls, generating compensation recommendations for company-fault cases, and finally producing agent guidance for all scenarios.

### Agent Roles

1. **RepeatCallDetector**: Determines if a call is related to a previous contact within 7 days by analyzing call history, product information, and issue similarity.

2. **FaultAnalyzer**: For repeat calls, assesses whether the issue is the company's responsibility by examining operational disruptions, usage patterns, and previous resolution attempts.

3. **CompensationRecommender**: Generates compensation recommendations for company-fault scenarios, considering customer lifetime value, issue severity, and previous compensations.

4. **CompensationReviewer**: Reviews compensation recommendations for fairness and consistency with company policy, approving or suggesting adjustments.

5. **RecommendationPublisher**: Creates practical guidance for call agents with talking points, technical solutions, and compensation details (if applicable).

### Group Chat Process

For company-fault cases, a structured conversation occurs:

1. **CompensationRecommender** generates an initial recommendation based on customer data and issue details.

2. **CompensationReviewer** starts the conversation by evaluating this recommendation, either approving it or suggesting changes.

3. If adjustments are suggested, the recommender responds to defend or refine their proposal.

4. This exchange continues until agreement is reached or maximum iterations are completed.

5. The final decision is incorporated into the call agent summary.

## Project Structure

```
repeated_calls_mvp_sample/
├── main.py                        # Main entry point for the application
├── src/                           # Source code directory
│   ├── processor.py               # Core processing logic
│   ├── agents.py                  # Agent definitions
│   ├── models.py                  # Data models
│   ├── data_loader.py             # Data loading utilities
│   └── __init__.py                # Package initialization
├── database/                      # Sample data for call analysis
│   ├── call_event.csv             # Current call events
│   ├── historic_call_event.csv    # Past call events
│   ├── customer.csv               # Customer information
│   ├── product.csv                # Product details
│   ├── subscription.csv           # Customer subscriptions
│   ├── discount.csv               # Available discounts
│   ├── software_update.csv        # Software update history
│   └── scenarios/                 # Test scenarios
├── output/                        # Generated recommendations saved here
│   └── [timestamp]_[call_id]/     # Output folder for each processed call
│       ├── recommendation.json    # Final recommendation and analysis
│       └── context/               # Context data used in analysis
│           ├── calls.json         # Current and historic call data
│           ├── customer.json      # Customer profile information
│           └── disruptions.json   # Relevant system disruptions
├── pyproject.toml                 # Project dependencies
└── .venv/                         # Virtual environment directory
```

## Installation

1. Install `uv` from [uv's installation guide](https://docs.astral.sh/uv/getting-started/installation/)

2. Clone and navigate to the repository:

   ```bash
   cd repeated_calls_mvp_sample
   ```

3. Create a virtual environment:

   ```bash
   uv venv
   ```

4. Activate the environment:

   **Linux/macOS**:

   ```bash
   source .venv/bin/activate
   ```

   **Windows**:

   ```bash
   .venv\Scripts\activate
   ```

5. Install dependencies:

   ```bash
   uv sync
   ```

## Usage

1. Create a `.env` file based on the example below and provide your Azure AI Foundry credentials:

   ```bash
   AZURE_OPENAI_CHAT_DEPLOYMENT_NAME=gpt-4o
   AZURE_OPENAI_ENDPOINT=
   AZURE_OPENAI_API_KEY=
   AZURE_OPENAI_API_VERSION=2025-03-01-preview
   ```

   Note: For best results, use a gpt-4o model deployment as it was used during development.

2. Run the script with a call event ID from the `database/call_event.csv` file:

   ```bash
   uv run main.py <call_event_id>
   ```

## Example Calls

### Example 1: AutoMow 3000 Issue (call ID: c1)

```bash
uv run main.py c1
```

**Summary**: Identifies a repeat call about an AutoMow 3000 mower not operating, determines it's the company's fault due to a software disruption, and recommends a $30 service credit as compensation.

### Example 2: HedgeBot Compact Power Issue (call ID: c2)

```bash
uv run main.py c2
```

**Summary**: Determines this is not a repeat call as it's about a HedgeBot Compact not turning on, which is unrelated to previous calls, and provides troubleshooting guidance without compensation.

### Example 3: HedgeBot Pro Wet Conditions Usage (call ID: c12)

```bash
uv run main.py c12
```

**Summary**: Identifies this as a repeat call about improper HedgeBot Pro usage in wet conditions, determines it's not the company's fault as it's contrary to product instructions, and recommends no compensation.

## Example Responses

Below are sample responses generated by the tool for each example call:

### Response for c1 (AutoMow 3000 Issue)

```json
{
  "customer_id": "7",
  "call_id": "c1",
  "timestamp": "2025-05-14T16:22:14.364181",
  "repeat_call_analysis": {
    "is_repeat_call": true,
    "related_call_ids": ["h1"],
    "days_since_first_call": 1,
    "issue_summary": "The AutoMow 3000 self-driving mower stops operating.",
    "reasoning": "The current call is about an unresolved issue with the same product (AutoMow 3000) that had been addressed in a previous call one day prior. The customer described similar symptoms, indicating the resolution of the prior call did not fully address the problem, making this a repeat call within the defined timeframe of 7 days."
  },
  "fault_analysis": {
    "is_our_fault": true,
    "fault_reason": "A known issue related to operational disruption during a software update affecting the AutoMow 3000, coupled with unresolved assurances.",
    "matching_disruption_ids": ["d7001"],
    "recommended_action": "Investigate the AutoMow 3000 for residual issues caused by the software update and ensure a permanent resolution, possibly offering compensation for inconvenience.",
    "reasoning": "The issue aligns with the disruption 'd7001' that affected the AutoMow 3000. Thus, it's linked to company operation. Additionally, resolution deadlines provided earlier were not met, contributing to recurring customer inconvenience."
  },
  "compensation_recommendation": {
    "recommended_compensation_type": "Service Credit",
    "amount": 150.0,
    "duration": "1 month",
    "justification": "Since the customer has a High CLV and experienced recurring issues with the AutoMow 3000, compensation is justified to address the inconvenience and maintain trust in our service.",
    "customer_value_consideration": "High CLV customer requires proactive and generous resolution measures to ensure continued satisfaction with the service."
  },
  "compensation_review": {
    "approved": true,
    "comments": "Approved. The recommended compensation of a $150 service credit is appropriate given the high CLV of the customer, the recurrence of the issue, and the inconvenience caused. It is consistent with company policy to address such situations with generosity to maintain customer satisfaction."
  },
  "call_agent_summary": {
    "one_sentence_recommendation": "Assist with immediate troubleshooting of the AutoMow 3000 and offer the approved $150 service credit for the inconvenience.",
    "compensation_details": "Approved $150 service credit for one month.",
    "technical_resolution": "Investigate and address residual issues related to the AutoMow 3000's software update disruption.",
    "customer_context": "High-value lifetime customer experiencing recurring issues with the AutoMow 3000, with a prior unresolved concern reported yesterday.",
    "talking_points": [
      "I'm here to assist with the issue you're facing with your AutoMow 3000.",
      "This issue has been identified as related to a software update disruption, and we're working on resolving it.",
      "We apologize for the inconvenience caused and have approved a $150 service credit to thank you for your patience.",
      "I'll walk you through some troubleshooting steps now to get your mower working again.",
      "If the issue persists, I'll ensure it is escalated for further investigation without delay."
    ],
    "next_steps": "Document the outcomes of the troubleshooting process, apply the $150 service credit to the customer's account, and escalate the issue to technical support if unresolved."
  },
  "conversation_history": {
    "messages": [
      {
        "name": "System",
        "content": "The following is a compensation review conversation. The initial recommendation is: {\n  \"recommended_compensation_type\": \"Service Credit\",\n  \"amount\": 150.0,\n  \"duration\": \"1 month\",\n  \"justification\": \"Since the customer has a High CLV and experienced recurring issues with the AutoMow 3000, compensation is justified to address the inconvenience and maintain trust in our service.\",\n  \"customer_value_consideration\": \"High CLV customer requires proactive and generous resolution measures to ensure continued satisfaction with the service.\"\n}. The reviewer will start by evaluating this recommendation, and then the recommender will respond to the reviewer's assessment.",
        "timestamp": "2025-05-14T16:22:10.493552"
      },
      {
        "name": "CompensationReviewer",
        "content": "{\"approved\":true,\"adjusted_amount\":null,\"adjusted_type\":null,\"comments\":\"Approved. The recommended compensation of a $150 service credit is appropriate given the high CLV of the customer, the recurrence of the issue, and the inconvenience caused. It is consistent with company policy to address such situations with generosity to maintain customer satisfaction.\"}",
        "timestamp": "2025-05-14T16:22:11.624825"
      }
    ]
  }
}
```

### Response for c2 (HedgeBot Compact Power Issue)

```json
{
  "customer_id": "22",
  "call_id": "c2",
  "timestamp": "2025-05-14T14:28:55.493520",
  "repeat_call_analysis": {
    "is_repeat_call": false,
    "related_call_ids": [],
    "issue_summary": "",
    "reasoning": "This call does not appear to be a repeat call because the reason for the current call concerns the HedgeBot Compact device not turning on, which is unrelated to the expired Aquaspray X promotion discussed in a prior call."
  },
  "call_agent_summary": {
    "one_sentence_recommendation": "Guide the customer through troubleshooting steps to resolve the HedgeBot Compact power issue.",
    "compensation_details": "No compensation is required for this call.",
    "technical_resolution": "Confirm that the device is connected properly to a power source and perform a reset using the reset button on the device.",
    "customer_context": "Andrew Lyons has been a high-value customer since March 2024 and owns two products from us, including a HedgeBot Compact.",
    "talking_points": [
      "Mr. Lyons, I'm here to assist you with your HedgeBot Compact not powering on.",
      "Let us confirm it is securely connected to a working power outlet.",
      "Please check if the reset button can help restore power to the device.",
      "I will guide you step-by-step to identify and resolve the issue."
    ],
    "next_steps": "If the troubleshooting steps do not resolve the issue, escalate it for a warranty claim or further technical support."
  },
  "conversation_history": {
    "messages": []
  }
}
```

### Response for c12 (HedgeBot Pro Wet Conditions Usage)

```json
{
  "customer_id": "45",
  "call_id": "c12",
  "timestamp": "2025-05-14T14:21:30.568292",
  "repeat_call_analysis": {
    "is_repeat_call": true,
    "related_call_ids": ["h17"],
    "days_since_first_call": 2,
    "issue_summary": "Usage of HedgeBot Pro in wet conditions leading to operational issues.",
    "reasoning": "The customer's history shows a previous call about encountering problems with their HedgeBot Pro after using it in rainy conditions, a violation of the user manual's usage guidelines. The current call relates to a similar issue, with the HedgeBot Pro exhibiting problems following usage in wet conditions. Since the calls are within a 2-day interval and concern the same product with issues arising from similar usage, the current call is considered a repeat call."
  },
  "fault_analysis": {
    "is_our_fault": false,
    "matching_disruption_ids": [],
    "recommended_action": "Educate the customer on proper usage as detailed in the device's user manual and offer a paid diagnostic service for the device.",
    "reasoning": "The issue appears to stem from the customer's use of the HedgeBot Pro to trim wet vegetation following rainy conditions, despite explicit warnings in the user manual that the device should not be exposed to moisture. This failure to adhere to recommended usage guidelines is a matter of user error rather than product fault. No relevant operational disruptions that could have impacted device functionality have been identified. The issue has already been explained as not covered under warranty in a previous call, and no evidence suggests a fault on the company's part."
  },
  "call_agent_summary": {
    "one_sentence_recommendation": "Provide the customer with guidance regarding the proper usage of the HedgeBot Pro and offer a paid diagnostic service.",
    "compensation_details": "No compensation is provided as the issue is due to user error, not product fault.",
    "technical_resolution": "Recommend that the customer refrains from using the HedgeBot Pro in wet conditions, as specified in the user manual, and suggest scheduling a diagnostic service.",
    "customer_context": "Customer Reagan Michael previously contacted the support team about issues arising from usage of HedgeBot Pro in wet conditions despite user manual recommendations; this is their second call with similar concerns within two days.",
    "talking_points": [
      "I understand you are experiencing issues with your HedgeBot Pro after using it to trim wet hedges.",
      "Please note that the user manual specifies that the HedgeBot Pro is not suitable for use in wet conditions, as moisture can interfere with its operation.",
      "This issue is not covered under warranty due to improper usage, as discussed during your previous call.",
      "To assist further, we can schedule a paid diagnostic service to check and possibly recover your device, or provide guidance on obtaining spare parts if necessary.",
      "Would you like to proceed with scheduling a diagnostic service?"
    ],
    "next_steps": "Document the interaction, update the system with the next service action if agreed upon, and ensure the customer's understanding of proper device usage."
  },
  "conversation_history": {
    "messages": []
  }
}
```
