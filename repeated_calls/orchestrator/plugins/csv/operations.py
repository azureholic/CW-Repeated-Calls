"""Plugins for the customer domain based on CSV files."""

import json
from typing import Annotated

from semantic_kernel.functions import kernel_function

from repeated_calls.database.schemas import SoftwareUpdate
from repeated_calls.utils.loggers import Logger

logger = Logger()


class OperationsDataPlugin:
    """Plugin with tools for retrieving customer data."""

    def __init__(self, data_path: str):
        """Initialize the plugin with the path to the CSV files."""
        self.software_updates = SoftwareUpdate.from_csv(f"{data_path}/software_update.csv")

    @kernel_function
    def get_software_updates(self, product_id: int) -> Annotated[str, "Software updates of the product."]:
        """Retrieve a JSON string of all software updates of the product."""
        # Find all software updates for the given product ID
        updates = [
            software_update.model_dump(mode="json")
            for software_update in self.software_updates
            if software_update.product_id == product_id
        ]

        if updates:
            return json.dumps(updates)

        logger.warning(f"Warning: No software updates found for product {product_id}")
        return "No software updates found"

    # Extra dummy function, always returns "No outages found"
    @kernel_function
    def check_outages(
        self, product_id: int
    ) -> Annotated[str, "Check if there is a current outage known for the product"]:
        """Retrieve a string whether a current outage is known for the product."""
        return "No outages found"
