import os
from pathlib import Path
from workspace_generator.models import BlueprintConfig

# Predefined order for grouping categories at the root level of the tree
GROUP_ORDER = ["index", "infra", "services", "apps", "jobs", "connectors", "libraries"]


def format_display_path(path: Path) -> str:
    """
    Normalizes path for display, replacing the user home directory with '~' 
    using Path.home() and Path.relative_to() logic, ensuring a trailing slash.
    """
    path = Path(path).resolve()
    home = Path.home().resolve()
    
    if path == home:
        display = "~"
    else:
        try:
            relative = path.relative_to(home)
            display = f"~/{relative}"
        except ValueError:
            display = str(path)
        
    if not display.endswith("/"):
        display += "/"
    return display


def generate_preview_tree(config: BlueprintConfig, workspace_dir: Path) -> str:
    """
    Dynamically generates the directory tree representing the planned workspace structure.
    Takes a pre-validated config model and targets paths. It does not parse YAML files directly.
    """
    # 1. Collect all planned repository target paths
    paths = []
    if config.repositories.index.enabled:
        paths.append(config.repositories.index.path)
    if config.repositories.infra.enabled:
        paths.append(config.repositories.infra.path)
    for component in config.components:
        if component.repository.path:
            paths.append(component.repository.path)

    # 2. Construct the nested tree representation
    tree = {}
    for p in sorted(paths):
        if not p:
            continue
        parts = Path(p).parts
        current = tree
        for part in parts:
            if part not in current:
                current[part] = {}
            current = current[part]

    # 3. Recursively build output lines using unicode characters
    def render_node(node: dict, prefix: str = "") -> list[str]:
        lines = []
        keys = list(node.keys())

        # Sort keys according to GROUP_ORDER, otherwise alphabetically
        def sort_key(k):
            if k in GROUP_ORDER:
                return (0, GROUP_ORDER.index(k), k)
            return (1, 0, k)

        keys.sort(key=sort_key)

        for i, key in enumerate(keys):
            is_last = (i == len(keys) - 1)
            connector = "└── " if is_last else "├── "
            lines.append(f"{prefix}{connector}{key}/")

            if node[key]:
                extension = "    " if is_last else "│   "
                lines.extend(render_node(node[key], prefix + extension))

        return lines

    tree_lines = render_node(tree)

    # 4. Construct final output format
    display_dir = format_display_path(workspace_dir)
    output_lines = [
        "Planned workspace structure:",
        "",
        display_dir
    ]
    output_lines.extend(tree_lines)
    return "\n".join(output_lines) + "\n"
