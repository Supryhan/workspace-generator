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
