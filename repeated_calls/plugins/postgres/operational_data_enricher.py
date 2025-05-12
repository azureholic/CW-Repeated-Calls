from sqlalchemy.orm import Session
from semantic_kernel.functions import kernel_function
from repeated_calls.database.tables import SoftwareUpdate

class OperationalDataEnricher:
    """
    A plugin to retrieve operational data, such as software updates, for a specific product.
    """

    def __init__(self, logger):
        self.logger = logger

    @kernel_function(name="retrieve_operational_data", description="Retrieve operational data for a product.")
    def retrieve_operational_data(self, session: Session, product_id: int):
        try:
            self.logger.info(f"Retrieving operational data for product_id={product_id}")
            updates = session.query(SoftwareUpdate).filter(SoftwareUpdate.product_id == product_id).all()
            update_descriptions = [update.description for update in updates]
            self.logger.info(f"Successfully retrieved {len(update_descriptions)} updates for product_id={product_id}")
            return update_descriptions
        except Exception as e:
            self.logger.error(f"Error retrieving operational data for product_id={product_id}: {e}")
            return []
