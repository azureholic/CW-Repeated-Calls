from datetime import timedelta
from time import sleep
from dapr.ext.workflow import (
    WorkflowRuntime,
    DaprWorkflowContext,
    WorkflowActivityContext,
    RetryPolicy,
    DaprWorkflowClient,
    when_any,
)
from dapr.conf import Settings
from dapr.clients.exceptions import DaprInternalError

settings = Settings()

counter = 0
retry_count = 0
child_orchestrator_count = 0
child_orchestrator_string = ''
child_act_retry_count = 0
instance_id = 'exampleInstanceID'
workflow_name = 'repeated_call_workflow'

input_data = 'Customer x called with topic y'
non_existent_id_error = 'no such instance exists'

retry_policy = RetryPolicy(
    first_retry_interval=timedelta(seconds=1),
    max_number_of_attempts=3,
    backoff_coefficient=2,
    max_retry_interval=timedelta(seconds=10),
    retry_timeout=timedelta(seconds=100),
)

wfr = WorkflowRuntime()


@wfr.workflow(name='repeated call workflow')
def repeated_call_workflow(ctx: DaprWorkflowContext, wf_input):
    print(f'{wf_input}')
    
    is_repeated = yield ctx.call_activity(is_repeated_call_activity, retry_policy=retry_policy)
    if is_repeated:
        is_our_fault = yield ctx.call_activity(is_our_fault_activity, retry_policy=retry_policy)

    # add more activities as needed
    return "Advice given to customer"


@wfr.activity(name='is_repeated_call_activity')
def is_repeated_call_activity(ctx: WorkflowActivityContext):
    # call agent here
    print('is repeated call activity executed')
    return True

@wfr.activity(name='is_our_fault_activity')
def is_our_fault_activity(ctx: WorkflowActivityContext):
    # call agent here
    print('is our fault activity executed')
    return True

def main():
    wfr.start()
    wf_client = DaprWorkflowClient()

    wf_client.schedule_new_workflow(
        workflow=repeated_call_workflow, input=input_data, instance_id=instance_id
    )

    wf_client.wait_for_workflow_start(instance_id)

    print('========= Waiting for Workflow completion', flush=True)
    try:
        state = wf_client.wait_for_workflow_completion(instance_id, timeout_in_seconds=30)
        if state.runtime_status.name == 'COMPLETED':
            print('Workflow completed! Result: {}'.format(state.serialized_output.strip('"')))
        else:
            print(f'Workflow failed! Status: {state.runtime_status.name}')
    except TimeoutError:
        print('*** Workflow timed out!')

    wf_client.purge_workflow(instance_id=instance_id)
    try:
        wf_client.get_workflow_state(instance_id=instance_id)
    except DaprInternalError as err:
        if non_existent_id_error in err._message:
            print('Instance Successfully Purged')

    wfr.shutdown()


if __name__ == '__main__':
    main()