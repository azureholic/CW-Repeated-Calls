import os
import datetime
from pathlib import Path

from azure.ai.evaluation import (
    GroundednessEvaluator,
    RelevanceEvaluator,
    SimilarityEvaluator,
    evaluate,
)
from dotenv import load_dotenv

load_dotenv()

azure_ai_project = {
    "subscription_id": os.getenv("AZURE_FOUNDRY_SUBSCRIPTION_ID"),
    "resource_group_name": os.getenv("AZURE_FOUNDRY_RESOURCE_GROUP_NAME"),
    "project_name": os.getenv("AZURE_FOUNDRY_PROJECT_NAME"),
}

# Base configuration shared by all models
base_config = {
    "azure_endpoint": os.getenv("AZURE_OPENAI_ENDPOINT"),
    "api_key": os.getenv("AZURE_OPENAI_API_KEY"),
    "api_version": os.getenv("AZURE_OPENAI_API_VERSION"),
}

# Define model deployments that will be used to judge the quality of the responses
model_judge_deployments = ["gpt-4o"]  # , "gpt-4o-mini", "Phi-4"]

# Create model configurations by combining base config with specific deployments
model_judge_configs = {
    model_judge_name: {**base_config, "azure_deployment": model_judge_name}
    for model_judge_name in model_judge_deployments
}


def get_output_path(dataset_path: str, model_name: str) -> str:
    """Generate output path with timestamp and model name."""
    dataset_name = Path(dataset_path).stem
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"results/eval_{dataset_name}_{model_name}_{timestamp}.json"


def run_evaluation(dataset_path: str):
    """Run evaluation for all models on the given dataset."""
    for model_judge_name, model_judge_config in model_judge_configs.items():
        groundedness_eval = GroundednessEvaluator(model_judge_config)
        relevance_eval = RelevanceEvaluator(model_judge_config)
        similarity_eval = SimilarityEvaluator(model_judge_config)

        output_path = get_output_path(dataset_path, model_judge_name)
        evaluation_name = output_path.replace("results/", "")

        evaluate(
            evaluation_name=evaluation_name,
            data=dataset_path,
            evaluators={
                "groundedness": groundedness_eval,
                "relevance": relevance_eval,
                "similarity": similarity_eval,
            },
            # evaluator_config={    # For single-turn chats
            #     "similarity": {
            #         "column_mapping": {
            #             "query": "${data.query}",
            #             "response": "${data.response}",
            #             "ground_truth": "${data.ground_truth}",
            #         }
            #     },
            #     "groundedness": {
            #         "column_mapping": {
            #             "context": "${data.context}",
            #             "response": "${data.response}",
            #         }
            #     },
            #     "relevance": {
            #         "column_mapping": {
            #             "query": "${data.query}",
            #             "response": "${data.response}",
            #         },
            #     },
            # },
            azure_ai_project=azure_ai_project,  # Makes the evaluation results available in the Foundry UI
            output_path=output_path,
        )
        print(f"Evaluation completed for {model_judge_name}. Results stored in: {output_path}")


if __name__ == "__main__":
    dataset_path = "datasets/conversations_repeated_call.jsonl"
    # dataset_path = "datasets/conversation_example.jsonl"
    # dataset_path = "datasets/single_turn_example.csv"

    run_evaluation(dataset_path)
