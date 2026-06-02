import os
import shutil
import tempfile
import unittest
import yaml
from pathlib import Path
from workspace_generator.config import load_config
from workspace_generator.models import BlueprintConfig
from workspace_generator.generator import WorkspaceGenerator
from workspace_generator.filesystem import resolve_path

class TestWorkspaceGenerator(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for sandboxed generation tests
        self.test_dir = tempfile.TemporaryDirectory()
        self.base_dir = Path(self.test_dir.name).resolve()

        # Create a sample valid blueprint YAML content
        self.blueprint_content = f"""
workspace:
  name: test-workspace
  display_name: Test Workspace
  base_directory: {self.base_dir}
  github_owner: testowner
  default_visibility: private
  repository_mode: starter

solution:
  name: test-solution
  display_name: Test Solution
  domain: education

environments:
  - local
  - DEV
  - SIT

repositories:
  index:
    enabled: true
    path: index
  infra:
    enabled: true
    path: infra

components:
  - name: test-api
    kind: service
    repository:
      path: services/test-api
      remote_name: test-workspace-test-api
    template: service-python-fastapi
    language: python
    framework: fastapi
    database: postgres
    port: 8000
    version: 0.2.0

  - name: test-lib
    kind: library
    repository:
      path: libraries/test-lib
      remote_name: test-workspace-test-lib
    template: component-empty
    language: typescript
    framework: none
    database: none
    # Omitting version to confirm '0.1.0' default
"""
        self.blueprint_file = self.base_dir / "test-blueprint.yaml"
        with open(self.blueprint_file, "w", encoding="utf-8") as f:
            f.write(self.blueprint_content)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_path_expansion(self):
        """
        Verify that resolve_path correctly expands home folders (~).
        """
        expanded = resolve_path("~/DEVELOPER/workspaces")
        self.assertTrue(expanded.is_absolute())
        self.assertEqual(expanded.name, "workspaces")
        self.assertEqual(expanded.parent.name, "DEVELOPER")
        self.assertTrue(str(expanded).startswith(os.path.expanduser("~")))

    def test_config_parsing_and_defaults(self):
        """
        Verify config loader successfully parses valid blueprint schema and defaults versions.
        """
        config = load_config(self.blueprint_file)
        self.assertIsInstance(config, BlueprintConfig)
        self.assertEqual(config.workspace.name, "test-workspace")
        self.assertEqual(config.solution.name, "test-solution")
        self.assertEqual(config.environments, ["local", "DEV", "SIT"])
        
        # Test defaults
        self.assertEqual(config.components[0].version, "0.2.0")
        # Second component omitted version, must default to 0.1.0
        self.assertEqual(config.components[1].version, "0.1.0")

    def test_invalid_config_schema(self):
        """
        Verify that schema errors (invalid kind or environment) throw Pydantic ValidationError.
        """
        invalid_yaml = """
workspace:
  name: test-workspace
  display_name: Test Workspace
  github_owner: testowner
environments:
  - INVALID_ENV_NAME
repositories:
  index:
    enabled: true
    path: index
  infra:
    enabled: true
    path: infra
components: []
"""
        invalid_file = self.base_dir / "invalid-blueprint.yaml"
        with open(invalid_file, "w", encoding="utf-8") as f:
            f.write(invalid_yaml)

        with self.assertRaises(ValueError) as ctx:
            load_config(invalid_file)
        self.assertIn("Blueprint configuration validation failed", str(ctx.exception))

    def test_dry_run_generation(self):
        """
        Verify that dry-run does not write any physical folders to disk.
        """
        generator = WorkspaceGenerator(safety_mode="dry-run", base_dir_override=self.base_dir)
        generator.generate(self.blueprint_file)

        # Workspace folder should not be created
        workspace_folder = self.base_dir / "test-workspace"
        self.assertFalse(workspace_folder.exists())

    def test_standard_generation_and_safe_modes(self):
        """
        Verify standard generation creates expected workspace and fail-if-exists blocks duplicates.
        """
        # Run generation
        generator = WorkspaceGenerator(safety_mode="fail-if-exists", base_dir_override=self.base_dir)
        generator.generate(self.blueprint_file)

        workspace_folder = self.base_dir / "test-workspace"
        self.assertTrue(workspace_folder.exists())

        # Test index repo files
        index_repo = workspace_folder / "index"
        self.assertTrue(index_repo.exists())
        self.assertTrue((index_repo / "README.md").exists())
        self.assertTrue((index_repo / "BLUEPRINT-SNAPSHOT.yaml").exists())
        self.assertTrue((index_repo / "VERSION").exists())

        # Verify no workspace-prefixed folders are generated (e.g., test-workspace-index)
        self.assertFalse((workspace_folder / "test-workspace-index").exists())
        self.assertFalse((workspace_folder / "test-workspace-infra").exists())
        self.assertFalse((workspace_folder / "test-workspace-test-api").exists())

        # Assert `.runtime/` is not generated eagerly
        self.assertFalse((workspace_folder / ".runtime").exists())

        # Test infra repo files
        infra_repo = workspace_folder / "infra"
        self.assertTrue(infra_repo.exists())
        gitignore_file = infra_repo / ".gitignore"
        self.assertTrue(gitignore_file.exists())
        with open(gitignore_file, "r") as f:
            self.assertIn(".runtime/", f.read())

        # Test compose override existence
        compose_override = infra_repo / "compose" / "compose.local.override.yml"
        self.assertTrue(compose_override.exists())

        # Test component repo files
        api_repo = workspace_folder / "services" / "test-api"
        self.assertTrue(api_repo.exists())
        self.assertTrue((api_repo / "VERSION").exists())
        with open(api_repo / "VERSION", "r") as vf:
            self.assertEqual(vf.read().strip(), "0.2.0")

        # Test fail-if-exists behavior on repeat execution
        with self.assertRaises(FileExistsError):
            generator.generate(self.blueprint_file)

    def test_force_and_skip_existing_safeties(self):
        """
        Verify --force overwrites and --skip-existing safely bypasses conflicts.
        """
        # Create pre-existing workspace folder
        workspace_folder = self.base_dir / "test-workspace"
        workspace_folder.mkdir(parents=True, exist_ok=True)
        dummy_file = workspace_folder / "dummy.txt"
        with open(dummy_file, "w") as f:
            f.write("preserve-me")

        # Skip existing mode should run without error
        generator_skip = WorkspaceGenerator(safety_mode="skip-existing", base_dir_override=self.base_dir)
        generator_skip.generate(self.blueprint_file)
        self.assertTrue(dummy_file.exists()) # Files preserved

        # Force mode runs and overwrites cleanly
        generator_force = WorkspaceGenerator(safety_mode="force", base_dir_override=self.base_dir)
        generator_force.generate(self.blueprint_file)
        # Verify generation succeeded
        self.assertTrue((workspace_folder / "index" / "README.md").exists())

    def test_database_component_isolation(self):
        """
        Verify dynamic Compose generators map separate database containers per database owner.
        """
        generator = WorkspaceGenerator(safety_mode="force", base_dir_override=self.base_dir)
        generator.generate(self.blueprint_file)

        infra_repo = self.base_dir / "test-workspace" / "infra"
        compose_file = infra_repo / "compose" / "compose.local.yml"
        self.assertTrue(compose_file.exists())

        with open(compose_file, "r") as f:
            compose_data = yaml.safe_load(f)

        services = compose_data.get("services", {})
        # test-api owns postgres, must have isolated db container
        self.assertIn("test-api", services)
        self.assertIn("test-api-db", services)
        # test-lib has no database, must NOT have a db container
        self.assertIn("test-lib", services)
        self.assertNotIn("test-lib-db", services)

    def test_version_manifest_generation(self):
        """
        Verify canonical YAML version manifests write SemVers and docker image details.
        """
        generator = WorkspaceGenerator(safety_mode="force", base_dir_override=self.base_dir)
        generator.generate(self.blueprint_file)

        infra_repo = self.base_dir / "test-workspace" / "infra"
        manifest_file = infra_repo / "versions" / "SIT.yaml"
        self.assertTrue(manifest_file.exists())

        with open(manifest_file, "r") as f:
            manifest_data = yaml.safe_load(f)

        self.assertEqual(manifest_data["workspace"], "test-workspace")
        self.assertEqual(manifest_data["environment"], "SIT")
        
        components = manifest_data.get("components", {})
        self.assertIn("test-api", components)
        self.assertEqual(components["test-api"]["version"], "0.2.0")
        self.assertEqual(components["test-api"]["image"], "test-workspace/test-api:0.2.0")

        self.assertIn("test-lib", components)
        self.assertEqual(components["test-lib"]["version"], "0.1.0")

if __name__ == "__main__":
    unittest.main()
