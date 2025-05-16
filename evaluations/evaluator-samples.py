"""
This file contains sample code for using the Azure AI Evaluation library. It
demonstrates how to use various evaluators for different tasks such as NLP
evaluation, AI-assisted quality evaluation, and risk and safety evaluation.
Solid documentation can be found here:
https://learn.microsoft.com/en-us/azure/ai-foundry/how-to/develop/evaluate-sdk

The evaluators were found here:
    - https://learn.microsoft.com/en-us/azure/ai-foundry/how-to/develop/evaluate-sdk#local-evaluation-on-test-datasets-using-evaluate
    - https://learn.microsoft.com/en-us/python/api/azure-ai-evaluation/azure.ai.evaluation?view=azure-python-preview

Evaluators that were not included in this sample:
    - RetrievalEvaluator
    - ResponseCompletenessEvaluator (seems to soon be deprecated(?))
    - UngroundedAttributesEvaluator (seems to soon be deprecated(?))
"""

# region Imports

import os
import json

from azure.identity import DefaultAzureCredential
from azure.ai.evaluation import (
    BleuScoreEvaluator,
    F1ScoreEvaluator,
    GleuScoreEvaluator,
    MeteorScoreEvaluator,
    RougeScoreEvaluator,
    RougeType,
    QAEvaluator,
    GroundednessEvaluator,
    GroundednessProEvaluator,
    RelevanceEvaluator,
    ViolenceEvaluator,
    CoherenceEvaluator,
    FluencyEvaluator,
    SimilarityEvaluator,
    SelfHarmEvaluator,
    HateUnfairnessEvaluator,
    IndirectAttackEvaluator,
    SexualEvaluator,
    ProtectedMaterialEvaluator,
    IndirectAttackEvaluator,
    ContentSafetyEvaluator,
    CodeVulnerabilityEvaluator,
)
from dotenv import load_dotenv

# endregion


# Helper function to print evaluator results
def print_evaluator_result(evaluator_name, result):
    print("=" * 28)
    print(evaluator_name.upper())
    print("=" * 28)
    print(json.dumps(result, indent=2) + "\n")


# region Configurations

# Load environment variables from .env file
load_dotenv()

model_config = {
    "azure_endpoint": os.getenv("AZURE_OPENAI_ENDPOINT"),
    "api_key": os.getenv("AZURE_OPENAI_API_KEY"),
    "azure_deployment": os.getenv("AZURE_OPENAI_DEPLOYMENT"),
    "api_version": os.getenv("AZURE_OPENAI_API_VERSION"),
}

azure_ai_project = {
    "subscription_id": os.getenv("AZURE_FOUNDRY_SUBSCRIPTION_ID"),
    "resource_group_name": os.getenv("AZURE_FOUNDRY_RESOURCE_GROUP_NAME"),
    "project_name": os.getenv("AZURE_FOUNDRY_PROJECT_NAME"),
}

# endregion

# region NLP Evaluators

# NLP F1 score evaluator
f1_score_evaluator = F1ScoreEvaluator()
result = f1_score_evaluator(
    response="The capital of Japan is Tokyo.",
    ground_truth="Tokyo is Japan's capital, known for its blend of traditional culture and technological advancements.",
)
print_evaluator_result("F1 Score Evaluator", result)

# NLP bleu score evaluator
bleu_score_evaluator = BleuScoreEvaluator()
result = bleu_score_evaluator(
    response="Tokyo is the capital of Japan.",
    ground_truth="The capital of Japan is Tokyo.",
)
print_evaluator_result("Bleu Score Evaluator", result)

# NLP gleu score evaluator
gleu_score_evaluator = GleuScoreEvaluator()
result = gleu_score_evaluator(
    response="Tokyo is the capital of Japan.",
    ground_truth="The capital of Japan is Tokyo.",
)
print_evaluator_result("Gleu Score Evaluator", result)

# NLP METEOR score evaluator
meteor_score_evaluator = MeteorScoreEvaluator(alpha=0.9, beta=3.0, gamma=0.5)
result = meteor_score_evaluator(
    response="Tokyo is the capital of Japan.",
    ground_truth="The capital of Japan is Tokyo.",
)
print_evaluator_result("Meteor Score Evaluator", result)

# NLP ROUGE score evaluator
rouge_score_evaluator = RougeScoreEvaluator(rouge_type=RougeType.ROUGE_1)
result = rouge_score_evaluator(
    response="Tokyo is the capital of Japan.",
    ground_truth="The capital of Japan is Tokyo.",
)
print_evaluator_result("Rouge Score Evaluator", result)

# endregion

# region AI-assisted quality evaluator

# AI-assisted groundedness evaluator
groundedness_evaluator = GroundednessEvaluator(model_config)
result = groundedness_evaluator(
    response="The capital of Japan is Tokyo.",
    context="Tokyo is Japan's capital, known for its blend of traditional culture and technological advancements.",
)
print_evaluator_result("Groundedness Evaluator", result)

# AI-assisted groundedness pro evaluator
groundedness_pro_evaluator = GroundednessProEvaluator(
    credential=DefaultAzureCredential(), azure_ai_project=azure_ai_project
)
result = groundedness_pro_evaluator(
    query="What's the capital of France",
    response="Paris",
    context="Paris is the capital of France.",
)
print_evaluator_result("Groundedness Pro Evaluator", result)

# AI-assisted relevance evaluator
relevance_evaluator = RelevanceEvaluator(model_config)
result = relevance_evaluator(
    query="What is the capital of Japan?", response="The capital of Japan is Tokyo."
)
print_evaluator_result("Relevance Evaluator", result)

# AI-assisted coherence evaluator
coherence_evaluator = CoherenceEvaluator(model_config)
result = coherence_evaluator(
    query="What is the capital of Japan?", response="The capital of Japan is Tokyo."
)
print_evaluator_result("Coherence Evaluator", result)

# AI-assisted fluency evaluator
fluency_evaluator = FluencyEvaluator(model_config)
result = fluency_evaluator(response="The capital of Japan is Tokyo.")
print_evaluator_result("Fluency Evaluator", result)

# AI-assisted similarity evaluator
similarity_evaluator = SimilarityEvaluator(model_config)
result = similarity_evaluator(
    query="What is the capital of Japan?",
    response="The capital of Japan is Tokyo.",
    ground_truth="Tokyo is Japan's capital.",
)
print_evaluator_result("Similarity Evaluator", result)

# endregion

# region AI-assisted risk and safety evaluators

# AI-assisted self-harm evaluator
self_harm_evaluator = SelfHarmEvaluator(
    credential=DefaultAzureCredential(), azure_ai_project=azure_ai_project
)
result = self_harm_evaluator(query="What is the capital of France?", response="Paris.")
print_evaluator_result("Self-Harm Evaluator", result)

# AI-assisted hateful and unfair evaluator
hate_unfairness_evaluator = HateUnfairnessEvaluator(
    credential=DefaultAzureCredential(), azure_ai_project=azure_ai_project
)
result = hate_unfairness_evaluator(
    query="What is the capital of France?", response="Paris."
)
print_evaluator_result("Hateful and Unfair Evaluator", result)

# AI-assisted violence evaluator
violence_evaluator = ViolenceEvaluator(
    credential=DefaultAzureCredential(), azure_ai_project=azure_ai_project
)
result = violence_evaluator(query="What is the capital of France?", response="Paris.")
print_evaluator_result("Violence Evaluator", result)

# AI-assisted sexual content evaluator
sexual_evaluator = SexualEvaluator(
    credential=DefaultAzureCredential(), azure_ai_project=azure_ai_project
)
result = sexual_evaluator(query="What is the capital of France?", response="Paris.")
print_evaluator_result("Sexual Content Evaluator", result)

# AI-assisted protected material evaluator
protected_material_evaluator = ProtectedMaterialEvaluator(
    credential=DefaultAzureCredential(), azure_ai_project=azure_ai_project
)
result = protected_material_evaluator(
    query="What is the capital of France?", response="Paris."
)
print_evaluator_result("Protected Material Evaluator", result)

# AI-assisted indirect attack evaluator
indirect_attack_evaluator = IndirectAttackEvaluator(
    credential=DefaultAzureCredential(), azure_ai_project=azure_ai_project
)
result = indirect_attack_evaluator(
    query="What is the capital of France?", response="Paris."
)
print_evaluator_result("Indirect Attack Evaluator", result)

# AI-assisted code vulnerability evaluator
code_vulnerability_evaluator = CodeVulnerabilityEvaluator(
    credential=DefaultAzureCredential(), azure_ai_project=azure_ai_project
)
result = code_vulnerability_evaluator(
    query="What is the capital of France?", response="Paris."
)
print_evaluator_result("Code Vulnerability Evaluator", result)

# endregion

# region Composite evaluators

# AI-assisted composite evaluator that contains all quality evaluators as well as F1 score
qa_eval = QAEvaluator(model_config)
result = qa_eval(
    query="Tokyo is the capital of which country?",
    response="Japan",
    context="Tokyo is the capital of Japan.",
    ground_truth="Japan",
)
print_evaluator_result("QA Evaluator", result)

# AI-assisted composite content safety evaluator that contains all risk and
# safety evaluators except protected material and indirect attack
content_safety_evaluator = ContentSafetyEvaluator(
    credential=DefaultAzureCredential(), azure_ai_project=azure_ai_project
)
result = content_safety_evaluator(
    query="What is the capital of France?", response="Paris."
)
print_evaluator_result("Content Safety Evaluator", result)

# endregion
