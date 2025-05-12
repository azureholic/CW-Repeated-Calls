from semantic_kernel.functions import kernel_function

class IngressProcessor:
    """
    A plugin to process incoming customer call data.
    """

    def __init__(self, logger):
        self.logger = logger

    @kernel_function(name="ingress_process", description="Process incoming customer call data.")
    def process_call(self, customer_id: int, call_reason: str):
        self.logger.info(f"Processing call for customer_id={customer_id}, call_reason={call_reason}")
        return {"customer_id": customer_id, "call_reason": call_reason}
