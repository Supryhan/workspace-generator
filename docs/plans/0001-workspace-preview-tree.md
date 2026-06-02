# Implementation Plan - Phase 7A: Workspace Preview Tree

This plan details the implementation of the Workspace Preview Tree feature. Before workspace generation starts, the CLI will output a planned directory tree of the workspace structure.

## User Review Required

> [!IMPORTANT]
> **Scope and Structure Constraints:**
> This feature only adds a console preview output before generation starts. It does not modify or impact the generated workspace directories, template logic, or files written to disk. No structural workspace changes are introduced.
> 
> **Module Responsibilities:**
> The rendering logic is isolated to the dedicated module `workspace_generator/preview.py`. This module is purely a presentation layer; it does not parse YAML blueprints directly. It only takes a pre-validated `BlueprintConfig` object and a resolved target `workspace_dir` path to produce the tree preview.
> 
> **Pydantic Schema Conformity:**
> All test blueprints and mock inputs in the plan conform to the validated schema restrictions of the `workspace_generator/models.py` schema:
> - Required `workspace` fields (e.g., `github_owner`, `name`, `display_name`).
> - Required `component` fields (e.g., `name`, `kind`, `repository.path`).
> - Valid choices for `kind` (`service`, `app`, `job`, `connector`, `library`), `repository_mode` (`starter`, `empty`, `template`), and `environments` (`local`, `DEV`, `SIT`, `UAT`, `PROD`).
> - Correct types for database, ports, language, version, and frameworks.
> - **Note on Ports:** The current schema expects the field `port` on `ComponentConfig`, rather than `internal_port` or `external_port`. All YAML snippets in the tests correctly use `port`.
> 
> **Test Safety (macOS resolution of `/tmp`):**
> On macOS, `/tmp` and `/var/tmp` are symlinks that resolve to `/private/tmp` and `/private/var/tmp`. To ensure assertions pass reliably across environments, tests checking format output avoid using `/tmp` in exact-string comparison assertions. Instead, they use a stable dummy path `/my-custom-base/` which does not resolve differently on macOS.

## Proposed Changes

---

### Workspace Generator Package

#### [NEW] [preview.py](file:///Users/vitaliisupryhan/DEVELOPER/workspace-generator/workspace_generator/preview.py)

Add a new module to handle the rendering of the tree format from a validated `BlueprintConfig` model. It utilizes `Path.home()` and `Path.relative_to()` for robust path formatting.

```python
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
```

#### [MODIFY] [generator.py](file:///Users/vitaliisupryhan/DEVELOPER/workspace-generator/workspace_generator/generator.py)

Integrate the preview rendering within the generation pipeline. The tree must be printed after configuration validation and before file generation starts, in both dry-run and real modes, without modifying the actual generated workspace structure.

```diff
  from pathlib import Path
  from workspace_generator.config import load_config
  from workspace_generator.models import BlueprintConfig, ComponentConfig
  from workspace_generator.renderer import TemplateRenderer
+ from workspace_generator.preview import generate_preview_tree
  from workspace_generator.filesystem import (
      resolve_path,
      safe_mkdir,
      safe_write,
      make_executable,
  )
```

```diff
          print(f"Generating workspace '{config.workspace.display_name}' under: {workspace_dir}")
          print(f"Solution: '{solution.display_name}'")
          print(f"Safety Mode: '{self.safety_mode}' | Repository Mode: '{config.workspace.repository_mode}'")
+ 
+         # Print planned workspace tree preview
+         print()
+         print(generate_preview_tree(config, workspace_dir), end="")
  
          # Check top-level conflict
          if workspace_dir.exists() and self.safety_mode == "fail-if-exists":
```

---

### Tests

#### [NEW] [test_preview.py](file:///Users/vitaliisupryhan/DEVELOPER/workspace-generator/tests/test_preview.py)

Add dedicated unit tests and integration tests verifying path formatting, tree generation logic, enabled repository inclusion/exclusion, and stdout matching. All mock blueprint snippets are fully compliant with the Pydantic schema validation constraints.

```python
import os
import tempfile
import unittest
import io
import contextlib
from pathlib import Path
from workspace_generator.config import load_config
from workspace_generator.preview import generate_preview_tree, format_display_path
from workspace_generator.generator import WorkspaceGenerator


class TestPreviewTree(unittest.TestCase):
    # --- Unit Tests ---

    def test_format_display_path_home_expansion(self):
        home = Path.home().resolve()
        path = home / "DEVELOPER" / "workspaces" / "product-catalog"
        display = format_display_path(path)
        self.assertEqual(display, "~/DEVELOPER/workspaces/product-catalog/")

    def test_format_display_path_non_home(self):
        # Using a dummy absolute base path to avoid /tmp resolving to /private/tmp on macOS
        path = Path("/my-custom-base/workspaces/product-catalog")
        display = format_display_path(path)
        self.assertEqual(display, "/my-custom-base/workspaces/product-catalog/")

    def test_generate_preview_tree(self):
        blueprint_content = """
workspace:
  name: product-catalog
  display_name: Product Catalog
  base_directory: ~/DEVELOPER/workspaces
  github_owner: test-owner
  default_visibility: private
  repository_mode: starter

environments:
  - local
  - DEV

repositories:
  index:
    enabled: true
    path: index
  infra:
    enabled: true
    path: infra

components:
  - name: catalog-service
    kind: service
    repository:
      path: services/catalog-service
      remote_name: example-org-catalog-service
    template: service-python-fastapi
    language: python
    framework: fastapi
    database: postgres
    port: 8000
    version: 0.1.0
  - name: web-frontend
    kind: app
    repository:
      path: apps/web-frontend
      remote_name: example-org-web-frontend
    template: component-empty
    language: typescript
    framework: nextjs
    database: none
    port: 3000
    version: 0.1.0
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(blueprint_content)
            temp_name = f.name

        try:
            config = load_config(Path(temp_name))
            home = Path.home().resolve()
            workspace_dir = home / "DEVELOPER" / "workspaces" / "product-catalog"
            
            preview = generate_preview_tree(config, workspace_dir)
            
            expected = (
                "Planned workspace structure:\n"
                "\n"
                "~/DEVELOPER/workspaces/product-catalog/\n"
                "├── index/\n"
                "├── infra/\n"
                "├── services/\n"
                "│   └── catalog-service/\n"
                "└── apps/\n"
                "    └── web-frontend/\n"
            )
            self.assertEqual(preview, expected)
        finally:
            os.remove(temp_name)
            
    def test_generate_preview_tree_disabled_repos(self):
        blueprint_content = """
workspace:
  name: simple-workspace
  display_name: Simple Workspace
  base_directory: /my-custom-base
  github_owner: test-owner
  default_visibility: private
  repository_mode: starter

environments:
  - local

repositories:
  index:
    enabled: false
    path: index
  infra:
    enabled: false
    path: infra

components:
  - name: my-lib
    kind: library
    repository:
      path: libraries/my-lib
      remote_name: example-org-my-lib
    template: component-empty
    language: typescript
    framework: none
    database: none
    port: null
    version: 0.1.0
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(blueprint_content)
            temp_name = f.name

        try:
            config = load_config(Path(temp_name))
            workspace_dir = Path("/my-custom-base/simple-workspace")
            preview = generate_preview_tree(config, workspace_dir)
            
            expected = (
                "Planned workspace structure:\n"
                "\n"
                "/my-custom-base/simple-workspace/\n"
                "└── libraries/\n"
                "    └── my-lib/\n"
            )
            self.assertEqual(preview, expected)
        finally:
            os.remove(temp_name)

    # --- Integration Tests ---

    def test_dry_run_preview_integration(self):
        """
        Verify that dry-run output contains the planned preview tree structure.
        Ensures individual path tokens are matched without expecting multi-level folder separators.
        """
        blueprint_content = """
workspace:
  name: product-catalog
  display_name: Product Catalog
  base_directory: ~/DEVELOPER/workspaces
  github_owner: test-owner
  default_visibility: private
  repository_mode: starter

environments:
  - local
  - DEV

repositories:
  index:
    enabled: true
    path: index
  infra:
    enabled: true
    path: infra

components:
  - name: catalog-service
    kind: service
    repository:
      path: services/catalog-service
      remote_name: example-org-catalog-service
    template: service-python-fastapi
    language: python
    framework: fastapi
    database: postgres
    port: 8000
    version: 0.1.0
  - name: web-frontend
    kind: app
    repository:
      path: apps/web-frontend
      remote_name: example-org-web-frontend
    template: component-empty
    language: typescript
    framework: nextjs
    database: none
    port: 3000
    version: 0.1.0
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(blueprint_content)
            temp_name = f.name

        try:
            generator = WorkspaceGenerator(safety_mode="dry-run", base_dir_override=tempfile.gettempdir())
            
            f_out = io.StringIO()
            with contextlib.redirect_stdout(f_out):
                generator.generate(Path(temp_name))
                
            output = f_out.getvalue()
            
            self.assertIn("Planned workspace structure:", output)
            self.assertIn("index/", output)
            self.assertIn("infra/", output)
            self.assertIn("services/", output)
            self.assertIn("catalog-service/", output)
            self.assertIn("apps/", output)
            self.assertIn("web-frontend/", output)
        finally:
            os.remove(temp_name)
```

## Verification Plan

### Automated Tests
- Run all unit and integration tests with verbose pytest:
  ```bash
  python3 -m pytest tests/ -v
  ```

### Manual Verification
- Execute a dry-run generation using the actual blueprint file and verify the printed planned workspace tree output visually:
  ```bash
  python3 -m workspace_generator create --config blueprints/product-catalog.example.yaml --dry-run
  ```
