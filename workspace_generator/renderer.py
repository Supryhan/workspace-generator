from pathlib import Path
from jinja2 import Environment, FileSystemLoader

# Resolve templates directory relative to workspace_generator package
TEMPLATES_DIR = Path(__file__).parent.parent / "templates"


class TemplateRenderer:
    """
    Manages loading and rendering Jinja2 templates using standard contexts.
    Templates are loaded from the top-level templates/ directory.
    """

    def __init__(self, templates_dir: Path = TEMPLATES_DIR):
        self.env = Environment(
            loader=FileSystemLoader(templates_dir),
            trim_blocks=True,
            lstrip_blocks=True,
            autoescape=False,
        )

    def render(self, template_name: str, context: dict) -> str:
        """
        Renders a Jinja2 template file with the given context dictionary.
        template_name is relative to the templates/ root (e.g. 'index/README.md.j2').
        """
        template = self.env.get_template(template_name)
        return template.render(**context)
