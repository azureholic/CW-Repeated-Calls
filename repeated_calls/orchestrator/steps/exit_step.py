"""Exit step for the process framework."""
from semantic_kernel.functions import kernel_function
from semantic_kernel.processes.kernel_process import KernelProcessStep


class ExitStep(KernelProcessStep):
    """Step to exit the process."""

    @kernel_function
    def exit(self) -> None:
        """Process function to exit the process."""
        print("ExitStep:\n\tExiting the process.")
