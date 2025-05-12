from sqlalchemy.orm import Session
from semantic_kernel.functions import kernel_function
from repeated_calls.database.tables import HistoricCallEvent

class HistoricalDataEnricher:
    """
    A plugin to retrieve historical call data for a customer.
    """

    def __init__(self, logger):
        self.logger = logger

    @kernel_function(name="retrieve_historical_data", description="Retrieve historical call data for the customer.")
    async def retrieve_historical_data(self, session: Session, customer_id: int):
        try:
            self.logger.info(f"Retrieving historical call data for customer_id={customer_id}")
            historical_data = session.query(HistoricCallEvent).filter(HistoricCallEvent.customer_id == customer_id).all()
            summaries = [event.call_summary for event in historical_data]
            self.logger.info(f"Successfully retrieved {len(summaries)} historical call summaries for customer_id={customer_id}")
            return summaries
        except Exception as e:
            self.logger.error(f"Error retrieving historical call data for customer_id={customer_id}: {e}")
            return []
