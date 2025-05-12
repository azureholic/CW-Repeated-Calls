import pandas as pd
from datetime import datetime, timedelta
from semantic_kernel.functions import kernel_function

class HistoricalDataEnricher:
    """
    A plugin to retrieve and analyze historical call data for a customer from a CSV file.
    """

    def __init__(self, logger, csv_file_path, llm):
        self.logger = logger
        self.csv_file_path = csv_file_path
        self.llm = llm

    @kernel_function(name="retrieve_historical_data", description="Retrieve and analyze historical call data for the customer.")
    def retrieve_historical_data(self, ingress_data: dict, history):
        try:
            customer_id = ingress_data.get("customer_id")
            sdc = ingress_data.get("sdc")
            ingress_time = ingress_data.get("time_stamp")

            self.logger.info(f"Retrieving historical call data for customer_id={customer_id} from CSV")

            df = pd.read_csv(self.csv_file_path)

            customer_data = df[df['customer_id'] == customer_id]

            if customer_data.empty:
                self.logger.warning(f"No historical call data found for customer_id={customer_id}")
                return []

            last_10_days = datetime.strptime(ingress_time, "%Y-%m-%d %H:%M:%S") - timedelta(days=10)
            customer_data['time_stamp'] = pd.to_datetime(customer_data['time_stamp'])
            recent_data = customer_data[customer_data['time_stamp'] >= last_10_days]

            if recent_data.empty:
                self.logger.warning(f"No historical call data found for customer_id={customer_id} in the last 10 days")
                return []

            historical_summaries = recent_data['call_summary'].tolist()
            prompt = (
                f"Customer issue: {sdc}\n"
                f"Historical call summaries:\n"
                f"{historical_summaries}\n\n"
                f"Identify the most relevant historical call summaries for the current issue."
            )

            self.logger.info("Using LLM to analyze historical call data")
            relevant_data = self.llm.invoke_prompt(prompt, chat_history=history)

            self.logger.info(f"Successfully retrieved relevant historical call summaries for customer_id={customer_id}")
            return relevant_data

        except Exception as e:
            self.logger.error(f"Error retrieving historical call data for customer_id={customer_id}: {e}")
            return []
