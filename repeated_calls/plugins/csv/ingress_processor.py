import pandas as pd
from semantic_kernel.functions import kernel_function
from semantic_kernel.contents import ChatHistory

class IngressProcessor:
    """
    A plugin to process incoming customer call data from a CSV file.
    """

    def __init__(self, logger, csv_file_path):
        self.logger = logger
        self.csv_file_path = csv_file_path

    @kernel_function(name="ingress_process", description="Process incoming customer call data.")
    def ingress_process(self, customer_id: int, chat_history: ChatHistory):
        try:
            self.logger.info(f"Processing call data for customer_id={customer_id} from CSV: {self.csv_file_path}")

            df = pd.read_csv(self.csv_file_path)
            customer_data = df[df['customer_id'] == customer_id]

            if customer_data.empty:
                message = f"No call event data found for customer_id={customer_id}"
                self.logger.warning(message)
                chat_history.add_message({"role": "system", "content": message})
                return {"message": message}

            
            call_event = customer_data.iloc[0].to_dict()
            sdc = call_event.get("sdc")
            time_stamp = call_event.get("time_stamp")
            
            success_message = f"Successfully retrieved call event data for customer_id={customer_id}"  
            self.logger.info(success_message)
            chat_history.add_message({
                "role": "system",
                "content": f"Call Event Data: {call_event}"
            })

            return {
                "call_event": call_event,
                "sdc": sdc,
                "time_stamp": time_stamp
            }

        except Exception as e:
            error_message = f"Error processing call data for customer_id={customer_id}: {e}"
            self.logger.error(error_message)
            chat_history.add_message({"role": "system", "content": error_message})
            return {"error": str(e)}
