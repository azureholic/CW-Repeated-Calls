"""
Module for managing Jinja2 templates for AI prompts.

This module provides classes for loading, managing, and rendering Jinja2 templates
for AI prompts. It includes:
- PromptTemplate: A class for loading and rendering a single template
- PromptTemplatePair: An abstract base class for managing system/user prompt pairs

Templates are used to generate structured prompts with variable content for
consistent interactions with AI models.
"""
import os
from abc import ABC
from importlib.resources import files
from typing import Any

from jinja2 import Environment, FileSystemLoader


class PromptTemplate:
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


class PromptTemplatePair(ABC):
    """Abstract base class for prompts that require both system and user prompts."""

    def __init__(self, user_template_name: str, system_template_name: str, template_dir: str | None = None) -> None:
        """Initialize system and user prompts with respective templates."""
        if template_dir is None:
            template_dir = str(next(iter(files("repeated_calls.prompt_engineering.templates")._paths)))
        self.user_prompt = PromptTemplate(template_dir, user_template_name)
        self.system_prompt = PromptTemplate(template_dir, system_template_name)

    def set_user_variable(self, key: str, value: Any) -> None:
        """Set a variable for the user prompt."""
        self.user_prompt.set_variable(key, value)

    def set_system_variable(self, key: str, value: Any) -> None:
        """Set a variable for the system prompt."""
        self.system_prompt.set_variable(key, value)

    def update_user_variables(self, new_vars: dict[str, Any]) -> None:
        """Update multiple variables for the user prompt."""
        self.user_prompt.update_variables(new_vars)

    def update_system_variables(self, new_vars: dict[str, Any]) -> None:
        """Update multiple variables for the system prompt."""
        self.system_prompt.update_variables(new_vars)

    def get_user_prompt(self) -> str:
        """Render and return the user prompt."""
        return self.user_prompt.render()

    def get_system_prompt(self) -> str:
        """Render and return the system prompt."""
        return self.system_prompt.render()
