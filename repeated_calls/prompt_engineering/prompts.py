"""
Module for managing prompt templates for AI interactions.

This module provides classes for loading, managing, and rendering Jinja2 templates
for AI prompts. It includes:
- _PromptTemplate: A class for loading and rendering a single template
- _PromptTemplateCollection: An abstract base class for managing system/user prompt collections
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

from repeated_calls.orchestrator.entities.state import State


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


class _PromptTemplateCollection(ABC):
    """Abstract base class for handling multiple named prompt templates."""

    def __init__(self, template_dir: str | None = None, **prompt_templates: str) -> None:
        """
        Initialize multiple named prompts using keyword arguments.

        Args:
            template_dir (str | None): Optional path to the directory containing templates.
            **prompt_templates: Arbitrary keyword arguments where the key is the prompt name
                                (e.g. 'user', 'system', 'reviewer_system') and the value is the template filename.
        """
        if template_dir is None:
            template_dir = str(next(iter(files("repeated_calls.prompt_engineering.templates")._paths)))

        self.prompts = {
            name: _PromptTemplate(template_dir, template_file) for name, template_file in prompt_templates.items()
        }

    def set_variable(self, prompt_name: str, key: str, value: Any) -> None:
        """Set a single variable for a specific named prompt."""
        self.prompts[prompt_name].set_variable(key, value)

    def update_variables(self, prompt_name: str, **kwargs) -> None:
        """Update multiple variables for a specific named prompt."""
        self.prompts[prompt_name].update_variables(kwargs)

    def get_prompt(self, prompt_name: str) -> str:
        """Render and return the specified named prompt."""
        return self.prompts[prompt_name].render()


class RepeatCallerPrompt(_PromptTemplateCollection):
    """Prompt class for determining repeated calls, managing both system and user prompts."""

    def __init__(self, state: State) -> None:
        """Initialise the RepeatCallerPrompt with specific templates."""
        super().__init__(user="repeat_caller_user.j2", system="repeat_caller_system.j2")

        for call in state.call_history:
            call.compute_time_since(state.call_event.timestamp)

        self.update_variables(
            prompt_name="user",
            customer=state.customer,
            call_event=state.call_event,
            call_timestamp=state.call_event.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            call_history=sorted(state.call_history, key=lambda h: h.start_time, reverse=True),
        )


class CausePrompt(_PromptTemplateCollection):
    """Prompt class for determining the cause of a product issue, managing both system and user prompts."""

    def __init__(self, state: State) -> None:
        """Initialise the CausePrompt with specific templates."""
        super().__init__(user="cause_user.j2", system="cause_system.j2")

        self.update_variables(
            prompt_name="user",
            call_event=state.call_event,
        )


class RecommendationPrompt(_PromptTemplateCollection):
    """Prompt class for generating personalized discount recommendations, managing both system and user prompts."""

    def __init__(self, state: State) -> None:
        """Initialise the RecommendationPrompt with specific templates."""
        super().__init__(
            user="recommendation_user.j2",
            system_recommendation="recommendation_system.j2",
            system_reviewer="reviewer_system.j2",
        )

        self.update_variables(
            prompt_name="user",
            call_event=state.call_event,
            cause_result=state.cause_result,
        )
