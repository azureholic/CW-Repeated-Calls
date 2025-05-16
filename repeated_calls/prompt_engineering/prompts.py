"""
Module for managing prompt templates for AI interactions.

This module provides classes for loading, managing, and rendering Jinja2 templates
for AI prompts. It includes:
- PromptTemplate: A class for loading and rendering a single template
- PromptTemplatePair: An abstract base class for managing system/user prompt pairs
- Specialized prompt classes specific stepts in the workflow:
    - RepeatCallerPrompt: For determining if a customer is a repeat caller
    - CausePrompt: For analyzing the cause of product issues
    - RecommendationPrompt: For generating personalized discount recommendations

Templates are rendered with context-specific data to generate structured prompts
for consistent and effective interactions with AI models across the repeated calls
workflow.
"""
import os
from abc import ABC
from importlib.resources import files
from typing import Any

from jinja2 import Environment, FileSystemLoader

from repeated_calls.orchestrator.entities.database import Discount
from repeated_calls.orchestrator.entities.state import State
from repeated_calls.orchestrator.entities.structured_output import CauseResult


class _PromptTemplate:
    """Base class for loading and rendering a single Jinja2 template."""

    def __init__(self, template_dir: str, template_name: str) -> None:
        """Initialize the prompt with a template directory and template name."""
        template_path = os.path.join(template_dir, template_name)
        if not os.path.exists(template_path):
            raise FileNotFoundError(f"Template '{template_name}' not found in '{template_dir}'")

        self.env = Environment(loader=FileSystemLoader(template_dir), autoescape=False)
        self.template = self.env.get_template(template_name)
        self.variables: dict[str, Any] = {}

    def set_variable(self, key: str, value: Any) -> None:
        """Set a template variable."""
        self.variables[key] = value

    def update_variables(self, new_vars: dict[str, Any]) -> None:
        """Bulk update of template variables."""
        self.variables.update(new_vars)

    def render(self) -> str:
        """Render the template with current variables."""
        return self.template.render(**self.variables)

    def __str__(self) -> str:
        """Easy string conversion to rendered prompt."""
        return self.render()


class _PromptTemplatePair(ABC):
    """Abstract base class for prompts that require both system and user prompts."""

    def __init__(self, user_template_name: str, system_template_name: str, template_dir: str | None = None) -> None:
        """Initialize system and user prompts with respective templates."""
        if template_dir is None:
            template_dir = str(next(iter(files("repeated_calls.prompt_engineering.templates")._paths)))
        self.user_prompt = _PromptTemplate(template_dir, user_template_name)
        self.system_prompt = _PromptTemplate(template_dir, system_template_name)

    def set_user_variable(self, key: str, value: Any) -> None:
        """Set a variable for the user prompt."""
        self.user_prompt.set_variable(key, value)

    def set_system_variable(self, key: str, value: Any) -> None:
        """Set a variable for the system prompt."""
        self.system_prompt.set_variable(key, value)

    def update_user_variables(self, **kwargs) -> None:
        """Update multiple variables for the user prompt."""
        self.user_prompt.update_variables(kwargs)

    def update_system_variables(self, **kwargs) -> None:
        """Update multiple variables for the system prompt."""
        self.system_prompt.update_variables(kwargs)

    def get_user_prompt(self) -> str:
        """Render and return the user prompt."""
        return self.user_prompt.render()

    def get_system_prompt(self) -> str:
        """Render and return the system prompt."""
        return self.system_prompt.render()


class RepeatCallerPrompt(_PromptTemplatePair):
    """Prompt class for determining repeated calls, managing both system and user prompts."""

    def __init__(self, state: State) -> None:
        """Initialise the RepeatCallerPrompt with specific templates."""
        super().__init__(user_template_name="repeat_caller_user.j2", system_template_name="repeat_caller_system.j2")

        for call in state.call_history:
            call.compute_time_since(state.call_event.timestamp)

        self.update_user_variables(
            customer=state.customer,
            call_event=state.call_event,
            call_timestamp=state.call_event.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            call_history=sorted(state.call_history, key=lambda h: h.start_time, reverse=True),
        )


class CausePrompt(_PromptTemplatePair):
    """Prompt class for determining the cause of a product issue, managing both system and user prompts."""

    def __init__(self, state: State) -> None:
        """Initialise the CausePrompt with specific templates."""
        super().__init__(user_template_name="cause_user.j2", system_template_name="cause_system.j2")

        self.update_user_variables(
            call_event=state.call_event,
        )


class RecommendationPrompt(_PromptTemplatePair):
    """Prompt class for formulating the offer recommendation, managing both system and user prompts."""

    def __init__(self, cause_result: CauseResult, customer_clv: str, matching_discount: Discount) -> None:
        """Initialise the RecommendationPrompt with specific templates."""
        super().__init__(user_template_name="recommendation_user.j2", system_template_name="recommendation_system.j2")

        self.update_user_variables(
            cause_result=cause_result,
            customer_clv=customer_clv,
            matching_discount=matching_discount,
        )
