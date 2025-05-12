# Scenario-Based Test Data Generation Guide

This guide explains how to create realistic, consistent test scenarios for GreenGarden Technology’s Customer Service System using structured JSON specifications and a reusable prompt template.

## Step 1: Define the Scenario

All scenarios must first be defined in a structured JSON format. These are stored in the `scenario_specifications.json` file. Each scenario describes:
 - The customer and their CLV status
 - The product involved
 - The timeline of the issue (current and past call dates)
 - The customer's reason for calling
 - System-level insights like software updates
 - Retention or goodwill offers
 - Recommended system response behavior

See `scenario_specification.json` for existing scenarios. 

## Step 2: Generate Call History and Events

Once your scenario JSON is ready, use the following prompt with ChatGPT or another generation agent to create the necessary call history and call_event rows. Make sure to replace `<<SCENARIO_JSON>>` with the JSON-description of your scenario that you defined in step 1.

**Prompt template**
```text
You are a data generator for our Customer Service System test environment.  
Given a scenario definition in JSON (see placeholder below), produce:

1. **A new `call_event` row** for the “primary_call_date” in the JSON, with:
   - A unique integer `id`
   - The `customer_id` from the JSON
   - An appropriate one-sentence `sdc` (self-described call reason) reflecting the “call_reason”. This cannot the be same as in the input json, but is something that a customer would say into the recording machine at the beginning of their service call.
   - A `time_stamp` on the primary call date (ISO 8601 datetime)

2. **One or more `historic_call_event` rows** for each date in `previous_call_dates`, with:
   - Unique integer `id` values
   - The same `customer_id`
   - The same or similar `sdc` as the primary call
   - A `call_summary` that:
     - Summarizes what was discussed (per `call_history_analysis`)
     - Mentions the promised resolution date
     - Does **not** mention any “operational_insight” items that were not yet known then
   - `start_time` and `end_time` datetimes on each historic date

Use these table schemas:
call_event:
  id: int
  customer_id: int
  sdc: str
  time_stamp: datetime str

historic_call_event:
  id: int
  customer_id: int
  sdc: str
  call_summary: str
  start_time: datetime str
  end_time: datetime str

The data you generate must be rows that can be added to existing CSV files with the schema specified above. 
The datetime format for all generated timestamps should be: YYYY-MM-DD HH:MM:SS

Expected system behavior (for validation in your tests):

    The system must detect this as a repeat call (per call_history_analysis).

    It must surface the operational_insight (e.g. recent software update) only after the new call starts.

    It must apply the retention strategy from customer_insights_and_retention_strategy when generating proposed responses.

Scenario JSON:

<<SCENARIO_JSON>>

Note: To generate everything correctly, your JSON must include:

    customer.customer_since (date the customer joined)

    product.monthly_price_eur (the lease price)

    (Optionally) any other product or customer fields your tests rely on.

If any of these are missing from your JSON spec, please add them.
```

## Step 3: Ensure data consistency

To ensure that each scenario is testable and aligns with our system logic, you must verify that all referenced data exists in the relevant system tables:
 - **Discounts:** Any offered discount (e.g. "20% off for 6 months") must exist in the discounts table, and it must be applicable to that customer and product based on the date and eligibility criteria.
 - **Software Updates:** If a scenario references a software update (as a possible cause of failure), a matching entry must be present in the software_updates table for the relevant product and date.
 - **Customers and Products:** The customer and product mentioned must exist in the customers and products tables.
 - **Subscriptions:** The customer must have an active subscription to the product at the time of the call (check the customer_subscriptions table or equivalent).

Failing to align scenario data with the actual database content will lead to test inconsistencies and incorrect system behavior during validation.

## Best Practices
 - Keep scenario names unique and descriptive.
 - Include both operational and emotional context in your scenario descriptions when applicable.
 - Always document system expectations and edge cases explicitly in scenario_details.