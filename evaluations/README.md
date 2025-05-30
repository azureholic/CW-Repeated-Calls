# Azure AI Evaluations

A sample project demonstrating the usage of Azure AI Evaluation SDK to evaluate AI model responses. This README contains findings from my experimentation with the SDK.

## Table of contents

- [Requirements](#requirements)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Findings](#findings)
  - [General information: evaluator types](#general-information-evaluator-types)
  - [Dataset requirements](#dataset-requirements)
  - [Evaluation approaches and considerations](#evaluation-approaches-and-considerations)
  - [Key takeaways for the repeated calls project](#key-takeaways-for-the-repeated-calls-project)
- [Additional opportunities to explore](#additional-opportunities-to-explore)
- [Documentation](#documentation)

## Requirements

- Python 3.12+
- Azure AI Foundry project (<https://ai.azure.com>). It can be either a Hub project or a Foundry project depending on what you would like to try. Hub projects are currently more stable.

## Installation

1. Install uv

   ```bash
   # On macOS/Linux
   curl -LsSf https://astral.sh/uv/install.sh | sh

   # On Windows (PowerShell)
   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```

   See the [uv installation documentation](https://docs.astral.sh/uv/getting-started/installation/) for more options.

2. Install dependencies

   ```bash
   # Create a virtual environment
   uv venv

   # Activate the virtual environment
   source .venv/bin/activate

   # On Windows (PowerShell)
   .venv\Scripts\Activate.ps1

   # Install dependencies
   uv sync
   ```

## Configuration

Create a `.env` file in the root directory (`evaluations/`) with the following variables (these can all be found in the Azure AI Foundry project(s) you should create here: <https://ai.azure.com>):

```bash
# Hub
AZURE_OPENAI_DEPLOYMENT=
AZURE_OPENAI_ENDPOINT=
AZURE_OPENAI_API_KEY=
AZURE_OPENAI_API_VERSION=
AZURE_FOUNDRY_SUBSCRIPTION_ID=
AZURE_FOUNDRY_RESOURCE_GROUP_NAME=
AZURE_FOUNDRY_PROJECT_NAME=

# Foundry
AI_FOUNDRY_PROJECT_ENDPOINT=
AI_FOUNDRY_AGENT_ID=
AI_FOUNDRY_MODEL_DEPLOYMENT_NAME=
AI_FOUNDRY_API_KEY=
AI_FOUNDRY_SUBSCRIPTION_ID=
AI_FOUNDRY_RESOURCE_GROUP_NAME=
AI_FOUNDRY_PROJECT_NAME=
AI_FOUNDRY_API_VERSION=

# Tracing
AZURE_TRACING_GEN_AI_CONTENT_RECORDING_ENABLED=true
```

## Usage

I have created various **standalone** scripts that serve as a guide for how to use the Azure AI Evaluation SDK:

- Run the sample evaluator script (demonstrates various evaluators with example inputs):

  ```bash
  uv run scripts/0_evaluator-samples.py
  ```

- Run the local evaluation script within a **Hub project** (evaluates dataset responses and makes the results available in the Azure AI Foundry UI):

  0. (The instructions below allow you to generate a dataset of conversations through the orchestrator, but it is not necessary to do it as you can utilise the already provided datasets in the `evaluations/datasets` folder, such as `4o_conversations_RepeatedCallDetector.jsonl` and `4o-mini_conversations_RepeatedCallDetector.jsonl`)

  1. First, run the orchestrator in the repeated_calls project to generate a dataset of conversations. The following command executes 3 different call events (`row_id`s) and saves the conversations to the `repeated_calls/conversation_logs` folder.

     ```bash
     rm -r repeated_calls/conversation_logs && for i in {1..3}; do poetry run python repeated_calls/orchestrator/main.py --loglevel DEBUG --row_id $i; done
     ```

  2. By running the orchestrator for multiple call events, the script generates a dataset of conversations that can be used as evaluation datasets for the evaluation script. The datasets are automatically saved to the `repeated_calls/conversation_logs/<AgentName>/all_conversations` folder. Once generated, copy the contents of the folder to the `evaluations/datasets` folder, and then run the following command to evaluate the dataset:

     ```bash
     uv run scripts/1_local_evaluation_hub.py --dataset datasets/4o_conversations_RepeatedCallDetector.jsonl
     ```

  3. The results are saved to the `evaluations/results` folder, as well as the Azure AI Foundry UI, which offers a visual representation of the results as well as a way to compare the results between different models (requires you to run the orchestrator multiple times with different models). The following image shows how the results look in the UI:

     ![ai-foundry-conversation-eval-comparison](images/ai-foundry-conversation-eval-comparison.png)

- (Broken) Run the local evaluation script within a **Foundry project** (attempts the same as the Hub project script, but with a Foundry project; unfortunately, it consistently gives a `500 Internal Server Error`):

  ```bash
  uv run scripts/1_local_evaluation_foundry.py --dataset datasets/conversations_RepeatedCallDetector.jsonl
  ```

- Run the continuous evaluation script within a Foundry project (usually gives a rate limit error, but occasionally works; see more details in the [Evaluation approaches and considerations](#evaluation-approaches-and-considerations) section):

  ```bash
  uv run scripts/2_continuous_evaluations.py
  ```

## Findings

### General information: evaluator types

There are multiple categories of ready-made evaluators. The AI-assisted quality metrics appear most promising for the repeated calls project. See the [API reference](https://learn.microsoft.com/en-us/python/api/azure-ai-evaluation/azure.ai.evaluation?view=azure-python) for a detailed description for each evaluator.

1. **AI-Assisted Quality Metrics:**
   - Groundedness
   - Relevance
   - Coherence
   - Fluency
   - Similarity
   - Retrieval (suitable for RAG evaluations)
2. **NLP Metrics:**
   - F1
   - BLEU
   - GLEU
   - METEOR
   - ROUGE
3. **AI-Assisted Risk and Safety Metrics:**
   - Self-harm
   - Hateful
   - Violent
   - Sexual
   - Protected material
   - Indirect attack
4. **Agent Evaluators:**
   - Intent Resolution
   - Tool Call Accuracy
   - Task Adherence
5. **Azure OpenAI Evaluators:**
   - Label grader
   - String checker
   - Text similarity
6. You also have the option to create [custom evaluators](https://learn.microsoft.com/en-us/azure/ai-foundry/concepts/evaluation-evaluators/custom-evaluators).

### Dataset requirements

Evaluation datasets can be provided in either `.jsonl` or `.csv` format. Two primary structures are supported:

#### A. Single-Turn Chats

This format is suitable for evaluating individual query-response interactions.

- **Columns:** (each evaluator requires different columns)

  - `query`: The user's input prompt or the scenario the model responded to.
  - `ground_truth`: The ideal or reference response, typically human-generated.
  - `response`: The response generated by the AI model to the query.
  - `context`: The source information on which the generated response is based (grounding information).

- **Example** (single-turn chat `.jsonl` format, one object per line, with the first object being actual `jsonl` and the second object being `json` for better readability):

  ```json
  {"query":"Customer reports that her RoboTrim X keeps stalling mid-session.","ground_truth":"Yes, this is a repeated call.","response":"The customer has previously reported that the RoboTrim X stalls during operation. The current call is about the same malfunction, with the product referenced by name and identical symptoms. This matches the prior issue and falls within a few days of the last call.","context":"Previous call (3 days ago): 'RoboTrim X keeps pausing randomly.' Summary: Diagnosed intermittent motor issue, pending technician visit."}
  {
    "query":"Caller says her garden mower won’t start this morning.",
    "ground_truth":"No, this is not a repeated call.",
    "response":"Although this call is about a garden mower, the last call was regarding a billing dispute for a fertilizer subscription. There is no overlap in the product or issue being discussed. Therefore, this is not a repeated call.",
    "context":"Previous call (5 days ago): 'I was charged twice for the premium fertilizer plan.' Summary: Resolved overbilling complaint."
  }
  ```

#### B. Conversations

This format is designed for evaluating multi-turn dialogues.

- **Structure:** each record in a `.jsonl` file is a JSON object containing a `conversation` key. The value is an object with a `messages` array. Each message object in the array includes:

  - `role`: indicates the speaker (e.g., `system`, `user`, `assistant`).
  - `content`: the text of the message.
  - `context` (necessary for the Groundedness evaluator for `assistant` messages)

- **Example:** (here in `json` format for readability)

  ```json
  {
    "conversation": {
      "messages": [
        {
          "role": "system",
          "content": "You are a customer service expert system. Determine if an incoming call is a repeat call. A repeat call concerns the same issue with the same product within the past month. Use call reasons and summaries to compare current and previous calls."
        },
        {
          "role": "user",
          "content": "## Customer Info\nID: 12\nName: Jamie Wu\n\n## Current Call\nCall Description: My AutoMow 3000 still shuts off mid-mow\nDate: 2025-05-10\n\n## Previous Calls\n- 2025-05-07: AutoMow 3000 stops halfway through mowing. Summary: Issue confirmed, troubleshooting started.\n- 2025-05-03: AutoMow 3000 keeps turning off. Summary: Customer reported repeated shutdowns. Asked to monitor behavior.\n\nIs this a repeat call?"
        },
        {
          "role": "assistant",
          "content": "{\"customer_id\":12,\"is_repeated_call\":true,\"conclusion\":\"Yes, this is a repeat call.\",\"analysis\":\"All calls are about the AutoMow 3000 shutting down mid-operation. The current call continues the same unresolved issue reported in earlier calls.\"}",
          "context": "## Customer Info\nID: 12\nName: Jamie Wu\n\n## Current Call\nCall Description: My AutoMow 3000 still shuts off mid-mow\nDate: 2025-05-10\n\n## Previous Calls\n- 2025-05-07: AutoMow 3000 stops halfway through mowing. Summary: Issue confirmed, troubleshooting started.\n- 2025-05-03: AutoMow 3000 keeps turning off. Summary: Customer reported repeated shutdowns. Asked to monitor behavior.\n\nIs this a repeat call?"
        }
      ]
    }
  }
  ```

### Evaluation approaches and considerations

#### A. Evaluations through code

Assuming the goal is to compare the quality of responses between different models:

- **Evaluation strategies:**

  - **Continuously evaluate production:** involves utilising capabilities like tracing, automatic evaluations, and A/B testing. This approach can be expensive (although sampling can be used to reduce costs). A guide on how to set this up is provided [here](https://learn.microsoft.com/en-us/azure/ai-foundry/how-to/continuous-evaluation-agents). I made an honest attempt at following the guide to make this work but I was not successful:

    - At first, I struggled due to trying to use a Hub project, while the guide is for Foundry projects. After this, I created a Foundry project and made another attempt.
    - The guide uses an old version of the SDK, so I had to rewrite the example code to use the latest version. The most recent documentation on handling AI Foundry agents I managed to find is [here](https://github.com/Azure/azure-sdk-for-python/tree/azure-ai-projects_1.0.0b11/sdk/ai/azure-ai-agents/samples), but it contains no information on evaluations.
    - I kept hitting rate limits when I did a simple `AgentEvaluationRequest`. A model redeploy or simply waiting some minutes sometimes (not always!) results in a successful evaluation (or it just randomly works, I can't say for sure).
      - I tried increasing rate limits of models to the maximum, but to no avail
      - This is a [known product-related issue](https://learn.microsoft.com/en-us/answers/questions/2237624/getting-rate-limit-exceeded-when-testing-ai-agent) and the recommended action is to wait...
    - Even if we would be able to get this to consistently work, I am not sure how the evaluation is truly "continuous", when for each time that you create an evaluation you have to provide a thread_id and run_id...
      - There is an option to sample the continuous evaluations to limit costs [here](https://learn.microsoft.com/en-us/azure/ai-foundry/how-to/continuous-evaluation-agents#customize-your-sampling-configuration) (if you can figure out how to actually make the evaluations continuous)
    - I could internally reach out to the person responsible for this documentation for further information, if desired.

  - **Evaluate production:** save queries and responses/conversations to a database, then perform data preparation and feed them to an evaluation script. This adds storage overhead.
    - I think this is currently the most practical approach for doing evaluations, along with evaluating test scenarios.
  - **Evaluate test scenarios:** run predefined test scenarios with different models. The risk is that these scenarios might not accurately represent production conversations.
    - I managed to implement this in the repeated calls project by capturing the conversations for each agent turn, then converting them to the expected `.jsonl` format, copy/pasting the dataset into the `evaluations/datasets` folder, and running the `1_local_evaluation_hub.py` script, using a Hub project. In this way, I could evaluate the quality of the responses of the different models.

- **Evaluation granularity (individual agent responses vs. whole loop output):**

  - **Individual agent responses:**
    - Offers more granular insights.
    - Can be done using `conversation` objects (as shown above).
    - Comparing models at the agent level is useful, as different agents might have different model requirements.
    - The `single-turn chat` format can also be adapted for individual agent response evaluation.
  - **Whole loop output:**
    - Simpler to implement but may be less useful for pinpointing specific areas for improvement.
    - Can be done using `single-turn chat` objects (e.g., `query` encapsulates all input, `response` is the final output, `context` includes intermediate steps/prompts).
    - **Challenge:** Identifying where to make improvements if the full loop response is insufficient.
    - **Note on groundedness:** The groundedness evaluator only requires `context` and `response`; so `ground_truth` is not always a necessity for evaluations.

- **Most interesting evaluators for the repeated calls project:**

  - Relevance and Groundedness
    - For these, I recommend generating conversational datasets since these evaluators don't require a ground truth. (I don't yet know whether conversational datasets support ground truth)
  - Similarity
    - For this, I recommend generating single-turn chat datasets since this evaluator requires a ground truth.
  - Perhaps custom evaluators would be useful for targeting more specifically whether a wrong or right answer is given for any given step (e.g., CorrectnessEvaluator).

- **Data preparation:**

  - A data preparation script will be needed to convert stored chat conversations into the expected `.jsonl` format (either conversations or single-turn chats).
  - For single-turn evaluations, careful consideration is needed for structuring the `context` (e.g., where/if to include system prompts) and defining the `query`.

- **Limitations encountered:**

  - Reasoning models (e.g., DeepSeek-R1, o4-mini) seem unsupported for acting as a judge in evaluations (like in `1_local_evaluation_hub.py`), yielding an error:

    ```bash
    openai.BadRequestError: Error code: 400 - {'error': {'message': "Unsupported parameter: 'max_tokens' is not supported with this model. Use 'max_completion_tokens' instead.", 'type': 'invalid_request_error', 'param': 'max_tokens', 'code': 'unsupported_parameter'}}
    ```

#### B. Azure AI Foundry (Hub project!) Evaluations (UI)

Hub projects within AI Foundry provide a user interface for conducting evaluations:

- **Automatic Evaluations:**

  - **"Evaluate a model":**
    - Well-suited for testing model performance on very specific tasks. Unfortunately does not allow you to choose an existing Foundry agent to evaluate with (you provide a system prompt for that specific evaluation).
    - Contains a feature to generate sample question/answer pairs using a GPT model, but this is limited to simple one-sentence questions and not ideal for large data inputs. I recommended to generate such data independently.
    - I encountered an "evalception" scenario, where my evaluation failed because my dataset contained a scenario with harmful content, which led Azure to block the evaluation.
  - **"Evaluate an existing query-response dataset":**
    - Highly useful for analyzing a response dataset. The "query" can represent all data the decision is based on.
    - Image: ![ai-foundry-evaluation](images/ai-foundry-evaluation.png)
    - It is also possible to compare evaluation results between different models. This can be used to compare different models as judges for the same dataset or to compare the response quality of different models.
    - Image: ![ai-foundry-evaluation-comparison](images/ai-foundry-evaluation-comparison.png)
  - **Note:** The Phi-4 model was not available in the Foundry UI at the time of testing, though it was accessible when running evaluation scripts locally.

- **Manual Evaluations:**

  - Allows you to manually give thumbs up or down for query/response datasets.
  - Not very useful beyond basic feedback collection. Could potentially serve as input for fine-tuning models.

- **Note:**
  - The evaluation SDK is relatively new. I encountered an installation error: [GitHub Issue #40992](https://github.com/Azure/azure-sdk-for-python/issues/40992) (`azure-ai-evaluations` installation).

#### C. Azure AI Foundry (Foundry project!) Evaluations (UI)

- Creating evaluations with manually generated datasets did not work (I kept receiving a `500 Internal Server Error`, even with very simple datasets that did work in a Hub project)
- Even creating evaluations with simulated questions did not work, getting the error `ArgumentInvalid: Evaluation data is required is invalid`

### Key takeaways for the repeated calls project

- The most practical approaches for evaluating the repeated calls project involve using the SDK scripts to either evaluate stored production data or run predefined test scenarios.
- For visual analysis and comparing models on datasets, the Azure AI Foundry (Hub project) UI, especially its "Dataset" evaluation feature, offers a viable and more stable alternative to the Foundry project UI.
- It will be crucial to develop a script that can convert existing chat logs into the required .jsonl format, supporting either "Single-Turn Chats" or "Conversations" structures.
- The choice of dataset format should be strategic: use the "Conversations" format for individual agent turn evaluations and for AI-assisted metrics like Relevance and Groundedness, while the "Single-Turn Chats" format is better for whole loop outputs or evaluators like Similarity that need a ground_truth field.
- For the specific needs of the repeated calls project, the AI-assisted evaluators "Relevance," "Groundedness," and "Similarity" appear to be the most promising.
- To address more specific requirements, such as directly assessing the correctness of the repeat call determination at each step, developing custom evaluators could be beneficial.
- The "continuous evaluation" approach using Foundry agents (as in `2_continuous_evaluations.py`) is currently unreliable due to persistent rate limiting issues, the SDK's maturity, and unclear steps for achieving true continuity, so it should not be prioritised.
- The user interface for evaluations within Foundry projects seems to have significant bugs, including `500` errors and problems with dataset loading, making Hub projects or code-based methods preferable for now.
- It is important to be aware that certain models, particularly some reasoning models like DeepSeek-R1, might not be directly compatible with the evaluation scripts due internal errors.
- Given that the `azure-ai-evaluation` SDK is relatively new, one should anticipate potential installation challenges and an API that may evolve over time, with risks of breaking changes.

## Additional opportunities to explore

Here are some promising areas that could enhance the evaluation strategy but were not yet explored:

- **Simulator for generating datasets**
  The simulator available via the Azure AI Evaluation SDK appears to have more potential than the simplistic one in the Foundry UI. It could help in creating realistic, large-scale datasets for training and evaluation.
  👉 [Simulator documentation](https://learn.microsoft.com/en-us/azure/ai-foundry/how-to/develop/simulator-interaction-data)

- **CI/CD evaluations**
  Integrating evaluation workflows directly into development pipelines could enable continuous quality control. These tools allow running evaluations automatically as part of GitHub Actions or Azure DevOps pipelines.

  - [GitHub Actions integration](https://learn.microsoft.com/en-us/azure/ai-foundry/how-to/evaluation-github-action)
  - [Azure DevOps integration](https://learn.microsoft.com/en-us/azure/ai-foundry/how-to/evaluation-azure-devops)

- **Red teaming for risk and safety**
  While this is outside quality evaluation, red teaming is useful for testing models against harmful, unsafe, or policy-violating content. Particularly useful for models in sensitive domains.
  👉 [Red teaming concepts](https://learn.microsoft.com/en-us/azure/ai-foundry/concepts/ai-red-teaming-agent)

## Documentation

For more information about Azure AI Evaluation, refer to:

- [Azure AI Evaluation SDK Documentation](https://learn.microsoft.com/en-us/azure/ai-foundry/how-to/develop/evaluate-sdk)
- [Azure AI Evaluation API Reference](https://learn.microsoft.com/en-us/python/api/azure-ai-evaluation/azure.ai.evaluation?view=azure-python-preview)
