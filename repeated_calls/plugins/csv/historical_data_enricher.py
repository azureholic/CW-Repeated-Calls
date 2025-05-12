import pandas as pd
from semantic_kernel.functions import kernel_function
from semantic_kernel.contents import ChatHistory

class HistoricalDataEnricher:
    """
    A plugin to retrieve historical call data for a customer from a CSV file and update the chat history.
    """

    def __init__(self, logger, csv_file_path):
        self.logger = logger
        self.csv_file_path = csv_file_path

    @kernel_function(name="retrieve_historical_data", description="Retrieve all historical call data for the customer and update chat history.")
    def retrieve_historical_data(self, customer_id: int, chat_history: ChatHistory):
        try:
            self.logger.info(f"Retrieving historical call data for customer_id={customer_id} from CSV: {self.csv_file_path}")

            df = pd.read_csv(self.csv_file_path)
            self.logger.debug(f"CSV file loaded successfully with {len(df)} records.")

            customer_data = df[df['customer_id'] == customer_id]

            if customer_data.empty:
                message = f"No historical call data found for customer_id={customer_id}"
                self.logger.warning(message)
                chat_history.add_message({"role": "system", "content": message})
                return {"message": message}

            historical_records = customer_data.to_dict(orient="records")

            success_message = f"Successfully retrieved historical call data for customer_id={customer_id}"
            self.logger.info(success_message)
            self.logger.debug(f"Historical Call Data: {historical_records}")
            chat_history.add_message({
                "role": "system",
                "content": f"Historical Call Data: {historical_records}"
            })

            return {"historical_data": historical_records}

        except Exception as e:
            # Handle any other exceptions
            error_message = f"Error retrieving historical call data for customer_id={customer_id}: {e}"
            self.logger.error(error_message, exc_info=True)
            chat_history.add_message({"role": "system", "content": error_message})
            return {"error": "Exception", "message": str(e)}