from semantic_kernel.functions import kernel_function

class RecommendationReviewer:
    """
    A plugin to review and validate recommendations for customers.
    """

    def __init__(self, logger):
        self.logger = logger

    @kernel_function(name="review_recommendation", description="Review and validate the recommendation.")
    def review_recommendation(self, recommendation: str):
        try:
            self.logger.info("Reviewing recommendation...")
            if not recommendation or len(recommendation.strip()) == 0:
                self.logger.warning("Recommendation is empty or invalid.")
                return "The recommendation is invalid. Please provide a valid recommendation."
            self.logger.info("Recommendation successfully reviewed and validated.")
            return recommendation
        except Exception as e:
            self.logger.error(f"Error reviewing recommendation: {e}")
            return "An error occurred while reviewing the recommendation."
