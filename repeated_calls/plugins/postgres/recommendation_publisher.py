from semantic_kernel.functions import kernel_function

class RecommendationPublisher:
    """
    A plugin to publish recommendations to a specified output channel.
    """

    def __init__(self, logger):
        self.logger = logger

    @kernel_function(name="publish_recommendation", description="Publish the recommendation to the output channel.")
    def publish_recommendation(self, recommendation: str):
        try:
            self.logger.info("Publishing recommendation...")
            self.logger.info(f"Recommendation published: {recommendation}")
            return "Recommendation successfully published."
        except Exception as e:
            self.logger.error(f"Error publishing recommendation: {e}")
            return "An error occurred while publishing the recommendation."
