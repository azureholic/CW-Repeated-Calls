import os, time
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from azure.ai.agents.models import ListSortOrder
from azure.ai.projects.models import EvaluatorIds
from azure.ai.projects.models import AgentEvaluationRequest
from azure.monitor.opentelemetry import configure_azure_monitor
from opentelemetry import trace


from dotenv import load_dotenv

load_dotenv()


project = AIProjectClient(
    credential=DefaultAzureCredential(), endpoint=os.getenv("AI_FOUNDRY_PROJECT_ENDPOINT")
)

configure_azure_monitor(connection_string=project.telemetry.get_connection_string())

scenario = os.path.basename(__file__)
tracer = trace.get_tracer(__name__)

with tracer.start_as_current_span(scenario):
    agent = project.agents.get_agent(agent_id=os.getenv("AI_FOUNDRY_AGENT_ID"))
    print(f"Agent: {agent.name}")

    thread = project.agents.threads.create()

    message = project.agents.messages.create(
        thread_id=thread.id, role="user", content="Please tell me a hilarious joke"
    )

    run = project.agents.runs.create_and_process(thread_id=thread.id, agent_id=agent.id)

    # Poll the run as long as run status is queued or in progress
    while run.status in ["queued", "in_progress", "requires_action"]:
        # Wait for a second
        time.sleep(3)
        run = project.agents.runs.get(thread_id=thread.id, run_id=run.id)
        print(f"Run status: {run.status}")

    if run.status == "failed":
        print(f"Run error: {run.last_error}")

    messages = project.agents.messages.list(thread_id=thread.id, order=ListSortOrder.ASCENDING)
    for msg in messages:
        if msg.text_messages:
            last_text = msg.text_messages[-1]
            print(f"{msg.role}: {last_text.text.value}")

    evaluators = {
        "Relevance": {"Id": EvaluatorIds.Relevance.value},
        "Fluency": {"Id": EvaluatorIds.Fluency.value},
        "Coherence": {"Id": EvaluatorIds.Coherence.value},
        # "Groundedness": {"Id": EvaluatorIds.Groundedness.value}, # NOT SUPPORTED
    }

    print("DEBUG: Got here 1")

    agent_evaluation_request = AgentEvaluationRequest(
        thread_id=thread.id,
        run_id=run.id,
        evaluators=evaluators,
        app_insights_connection_string=project.telemetry.get_connection_string(),
    )

    print("DEBUG: Got here 2")

    agent_evaluation = project.evaluations.create_agent_evaluation(
        evaluation=agent_evaluation_request
    )

    print("DEBUG: Got here 3")

    while agent_evaluation.status == "Running":
        time.sleep(1)
        agent_evaluation = project.evaluations.get(agent_evaluation.id)

    print(agent_evaluation)
