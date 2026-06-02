import yaml
from pathlib import Path
from pydantic import ValidationError
from workspace_generator.models import BlueprintConfig


def load_config(file_path: str | Path) -> BlueprintConfig:
    """
    Reads a YAML blueprint file, parses it, and validates it against Pydantic models.
    Raises FileNotFoundError, ValueError on missing/invalid files.
    """
    path = Path(file_path).expanduser().resolve()
    if not path.exists():
        raise FileNotFoundError(f"Workspace blueprint not found at: {path}")

    with open(path, "r", encoding="utf-8") as f:
        try:
            data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML syntax in workspace blueprint: {e}")

    if not data or not isinstance(data, dict):
        raise ValueError("Workspace blueprint is empty or not a valid dictionary structure.")

    try:
        config = BlueprintConfig(**data)
    except ValidationError as e:
        error_messages = []
        for error in e.errors():
            loc = " -> ".join(str(x) for x in error["loc"])
            msg = error["msg"]
            error_messages.append(f"  Field '{loc}': {msg}")
        raise ValueError("Blueprint configuration validation failed:\n" + "\n".join(error_messages))

    return config
