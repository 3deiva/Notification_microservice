from jinja2 import Environment, BaseLoader, TemplateError
from typing import Any
from app.templates.message_templates import TEMPLATES
from app.config.logging import get_logger

logger = get_logger(__name__)
jinja_env = Environment(loader=BaseLoader())


class TemplateProcessor:
    """Renders notification message templates."""

    @staticmethod
    def render(event_type: str, context: dict[str, Any]) -> dict[str, str]:
        """
        Returns rendered template dict with keys like 'sms', 'subject', 'body'
        depending on the channel.
        """
        template_config = TEMPLATES.get(event_type)
        if not template_config:
            raise ValueError(f"No template found for event_type: {event_type}")

        result = {"channel": template_config["channel"]}
        try:
            if template_config["channel"] == "sms":
                tmpl = jinja_env.from_string(template_config["sms"])
                result["sms"] = tmpl.render(**context)
            elif template_config["channel"] == "email":
                subject_tmpl = jinja_env.from_string(template_config["subject"])
                body_tmpl = jinja_env.from_string(template_config["body"])
                result["subject"] = subject_tmpl.render(**context)
                result["body"] = body_tmpl.render(**context)
        except TemplateError as e:
            logger.error("template_render_error", event_type=event_type, error=str(e))
            raise

        return result
