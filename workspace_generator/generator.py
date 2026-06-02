from pathlib import Path
from workspace_generator.config import load_config
from workspace_generator.models import BlueprintConfig, ComponentConfig
from workspace_generator.renderer import TemplateRenderer
from workspace_generator.filesystem import (
    resolve_path,
    safe_mkdir,
    safe_write,
    make_executable,
)

# Maps component kind to the generated folder group under the workspace root
KIND_FOLDER_MAP = {
    "service": "services",
    "app": "apps",
    "job": "jobs",
    "connector": "connectors",
    "library": "libraries",
}


class WorkspaceGenerator:
    """
    Orchestrates the full workspace generation from a YAML blueprint.

    Terminology:
    - workspace: local filesystem container at ~/DEVELOPER/workspaces/<name>/
    - solution:  the business/domain system represented by the workspace
    - component: internal umbrella term for any repository entry (service, app, job, connector, library)
    - kind:      the functional role of a component, determines the generated folder group
    """

    def __init__(
        self,
        safety_mode: str = "fail-if-exists",
        base_dir_override: str | Path | None = None,
    ):
        allowed_modes = {"fail-if-exists", "force", "skip-existing", "dry-run"}
        if safety_mode not in allowed_modes:
            raise ValueError(
                f"Invalid safety mode: '{safety_mode}'. Choose from {allowed_modes}"
            )
        self.safety_mode = safety_mode
        self.base_dir_override = resolve_path(base_dir_override) if base_dir_override else None
        self.renderer = TemplateRenderer()

    def generate(self, blueprint_path: str | Path) -> None:
        """
        Parses a YAML blueprint and triggers full workspace rendering.
        """
        blueprint_file = resolve_path(blueprint_path)
        config = load_config(blueprint_file)

        # Resolve base workspaces directory
        if self.base_dir_override:
            base_dir = self.base_dir_override
        else:
            base_dir = resolve_path(config.workspace.base_directory)

        workspace_dir = base_dir / config.workspace.name
        solution = config.effective_solution()

        print(f"Generating workspace '{config.workspace.display_name}' under: {workspace_dir}")
        print(f"Solution: '{solution.display_name}'")
        print(f"Safety Mode: '{self.safety_mode}' | Repository Mode: '{config.workspace.repository_mode}'")

        # Check top-level conflict
        if workspace_dir.exists() and self.safety_mode == "fail-if-exists":
            raise FileExistsError(
                f"Error: Target workspace directory '{workspace_dir}' already exists. "
                "Use --force to overwrite or --skip-existing to bypass conflicts safely."
            )

        dry_run = self.safety_mode == "dry-run"
        force = self.safety_mode == "force"

        if not dry_run:
            safe_mkdir(workspace_dir, dry_run=False)

        context = {
            "workspace": config.workspace,
            "solution": solution,
            "components": config.components,
            "environments": config.environments,
        }

        # Generate index repository
        if config.repositories.index.enabled:
            self._generate_index(workspace_dir, config, blueprint_file, context, dry_run, force)

        # Generate infrastructure repository
        if config.repositories.infra.enabled:
            self._generate_infra(workspace_dir, config, context, dry_run, force)

        # Generate component repositories grouped by kind
        for component in config.components:
            self._generate_component(workspace_dir, config, component, context, dry_run, force)

        print("\nWorkspace generation completed successfully!")

    # -------------------------------------------------------------------------
    # Index Repository
    # -------------------------------------------------------------------------

    def _generate_index(
        self,
        workspace_dir: Path,
        config: BlueprintConfig,
        blueprint_file: Path,
        context: dict,
        dry_run: bool,
        force: bool,
    ) -> None:
        index_path = workspace_dir / config.repositories.index.path
        print(f"\n--> Configuring Workspace Index Repository: {index_path.name}/")

        if index_path.exists() and self.safety_mode == "fail-if-exists" and not force:
            raise FileExistsError(
                f"Index repository directory '{index_path}' already exists."
            )
        if index_path.exists() and self.safety_mode == "skip-existing":
            print(f"  [SKIPPED] Index repository already exists: {index_path.name}/")
            return

        safe_mkdir(index_path, dry_run)
        safe_mkdir(index_path / "scripts", dry_run)
        safe_mkdir(index_path / "docs", dry_run)
        safe_mkdir(index_path / ".github" / "workflows", dry_run)

        # Core markdown files
        template_files = {
            "README.md": "index/README.md.j2",
            "WORKSPACE-CARD.md": "index/WORKSPACE-CARD.md.j2",
            "COMPONENTS.md": "index/COMPONENTS.md.j2",
            "REPOSITORIES.md": "index/REPOSITORIES.md.j2",
            "ROADMAP.md": "index/ROADMAP.md.j2",
            "STATUS.md": "index/STATUS.md.j2",
            ".gitignore": "index/.gitignore.j2",
        }

        for fname, template in template_files.items():
            content = self.renderer.render(template, context)
            safe_write(index_path / fname, content, dry_run, force)

        # VERSION — plain write
        safe_write(index_path / "VERSION", "0.1.0\n", dry_run, force)

        # BLUEPRINT-SNAPSHOT.yaml — copy of the source blueprint
        if blueprint_file.exists():
            with open(blueprint_file, "r", encoding="utf-8") as bf:
                snap_content = bf.read()
            safe_write(index_path / "BLUEPRINT-SNAPSHOT.yaml", snap_content, dry_run, force)

        # CI workflow for the index repo
        index_component = ComponentConfig(
            name=f"{config.workspace.name}-index",
            kind="service",
            repository={"path": config.repositories.index.path, "remote_name": None},
            language="markdown",
            framework="none",
            version="0.1.0",
        )
        ci_content = self.renderer.render(
            "repository/.github/workflows/ci.yml.j2",
            {**context, "component": index_component},
        )
        safe_write(index_path / ".github" / "workflows" / "ci.yml", ci_content, dry_run, force)

    # -------------------------------------------------------------------------
    # Infrastructure Repository
    # -------------------------------------------------------------------------

    def _generate_infra(
        self,
        workspace_dir: Path,
        config: BlueprintConfig,
        context: dict,
        dry_run: bool,
        force: bool,
    ) -> None:
        infra_path = workspace_dir / config.repositories.infra.path
        print(f"\n--> Configuring Infrastructure Repository: {infra_path.name}/")

        if infra_path.exists() and self.safety_mode == "fail-if-exists" and not force:
            raise FileExistsError(
                f"Infrastructure repository directory '{infra_path}' already exists."
            )
        if infra_path.exists() and self.safety_mode == "skip-existing":
            print(f"  [SKIPPED] Infrastructure repository already exists: {infra_path.name}/")
            return

        safe_mkdir(infra_path, dry_run)
        safe_mkdir(infra_path / "compose", dry_run)
        safe_mkdir(infra_path / "env", dry_run)
        safe_mkdir(infra_path / "versions", dry_run)
        safe_mkdir(infra_path / "port-forwarding", dry_run)
        # NOTE: .runtime/ is NOT generated here — it is transient runtime state.
        # start-port-forwarding.sh creates .runtime/port-forwarding/ on demand.
        safe_mkdir(infra_path / "scripts", dry_run)
        safe_mkdir(infra_path / "docs", dry_run)

        # Core files
        safe_write(
            infra_path / "README.md",
            self.renderer.render("infra/README.md.j2", context),
            dry_run, force,
        )
        safe_write(
            infra_path / ".gitignore",
            self.renderer.render("infra/.gitignore.j2", context),
            dry_run, force,
        )
        safe_write(infra_path / "VERSION", "0.1.0\n", dry_run, force)

        # Docker Compose configurations
        safe_write(
            infra_path / "compose" / "compose.local.yml",
            self.renderer.render("infra/compose/compose.local.yml.j2", context),
            dry_run, force,
        )
        safe_write(
            infra_path / "compose" / "compose.local.override.yml",
            self.renderer.render("infra/compose/compose.local.override.yml.j2", context),
            dry_run, force,
        )
        for env in ["DEV", "SIT", "UAT", "PROD"]:
            safe_write(
                infra_path / "compose" / f"compose.{env}.yml",
                self.renderer.render(f"infra/compose/compose.{env}.yml.j2", context),
                dry_run, force,
            )

        # Per-environment: env files, version manifests, port-forwarding configs
        for env in config.environments:
            env_context = {**context, "env_name": env}
            safe_write(
                infra_path / "env" / f"{env}.example.env",
                self.renderer.render("infra/env/env.j2", env_context),
                dry_run, force,
            )
            safe_write(
                infra_path / "versions" / f"{env}.yaml",
                self.renderer.render("infra/versions/version_manifest.yaml.j2", env_context),
                dry_run, force,
            )
            safe_write(
                infra_path / "port-forwarding" / f"{env}.yaml",
                self.renderer.render("infra/port-forwarding/forwarding.yaml.j2", env_context),
                dry_run, force,
            )

        # Documentation guides
        docs = [
            "ENVIRONMENTS.md",
            "DEPLOYMENT.md",
            "COMPONENTS.md",
            "LOCAL-DEBUG.md",
            "PORT-FORWARDING.md",
            "VERSIONING.md",
        ]
        for doc in docs:
            safe_write(
                infra_path / "docs" / doc,
                self.renderer.render(f"infra/docs/{doc}.j2", context),
                dry_run, force,
            )

        # Infrastructure scripts (all marked executable)
        scripts = [
            "start-local.sh",
            "stop-local.sh",
            "reset-local.sh",
            "logs.sh",
            "smoke-test.sh",
            "start-with-local-component.sh",
            "stop-with-local-component.sh",
            "start-port-forwarding.sh",
            "stop-port-forwarding.sh",
            "status-port-forwarding.sh",
            "check-versions.sh",
            "validate-compatibility.sh",
        ]
        for script in scripts:
            spath = infra_path / "scripts" / script
            safe_write(
                spath,
                self.renderer.render(f"infra/scripts/{script}.j2", context),
                dry_run, force,
            )
            make_executable(spath, dry_run)

    # -------------------------------------------------------------------------
    # Component Repositories
    # -------------------------------------------------------------------------

    def _generate_component(
        self,
        workspace_dir: Path,
        config: BlueprintConfig,
        component: ComponentConfig,
        context: dict,
        dry_run: bool,
        force: bool,
    ) -> None:
        # Resolve local path from component.repository.path relative to workspace_dir
        comp_path = workspace_dir / component.repository.path
        print(f"\n--> Configuring {component.kind.capitalize()} Repository: {component.repository.path}/")

        if comp_path.exists() and self.safety_mode == "fail-if-exists" and not force:
            raise FileExistsError(
                f"Repository directory '{comp_path}' already exists."
            )
        if comp_path.exists() and self.safety_mode == "skip-existing":
            print(f"  [SKIPPED] Repository already exists: {component.repository.path}/")
            return

        safe_mkdir(comp_path, dry_run)
        safe_mkdir(comp_path / "src", dry_run)
        safe_mkdir(comp_path / "tests", dry_run)
        safe_mkdir(comp_path / "docs", dry_run)
        safe_mkdir(comp_path / "scripts", dry_run)
        safe_mkdir(comp_path / ".github" / "workflows", dry_run)

        comp_context = {**context, "component": component}

        # Base files required by all components
        safe_write(
            comp_path / "README.md",
            self.renderer.render("repository/README.md.j2", comp_context),
            dry_run, force,
        )
        safe_write(
            comp_path / ".gitignore",
            self.renderer.render("repository/.gitignore.j2", comp_context),
            dry_run, force,
        )
        safe_write(
            comp_path / "VERSION",
            self.renderer.render("repository/VERSION.j2", comp_context),
            dry_run, force,
        )

        # Empty repository mode: only gitkeep placeholders
        if config.workspace.repository_mode == "empty":
            safe_write(comp_path / "src" / ".gitkeep", "", dry_run, force)
            safe_write(comp_path / "tests" / ".gitkeep", "", dry_run, force)
            safe_write(comp_path / "docs" / ".gitkeep", "", dry_run, force)
            safe_write(comp_path / "scripts" / ".gitkeep", "", dry_run, force)
            return

        # Starter / template mode
        safe_write(
            comp_path / "PROJECT-CARD.md",
            self.renderer.render("repository/PROJECT-CARD.md.j2", comp_context),
            dry_run, force,
        )
        safe_write(
            comp_path / "AGENTS.md",
            self.renderer.render("repository/AGENTS.md.j2", comp_context),
            dry_run, force,
        )
        safe_write(
            comp_path / "Dockerfile",
            self.renderer.render("repository/Dockerfile.j2", comp_context),
            dry_run, force,
        )
        safe_write(
            comp_path / ".env.example",
            self.renderer.render("repository/.env.example.j2", comp_context),
            dry_run, force,
        )
        safe_write(
            comp_path / ".github" / "workflows" / "ci.yml",
            self.renderer.render("repository/.github/workflows/ci.yml.j2", comp_context),
            dry_run, force,
        )

        # Language-specific source placeholders
        lang = component.language or ""
        if lang in ("typescript", "javascript"):
            safe_write(
                comp_path / "src" / "index.ts",
                'console.log("Starting {{ component.name }}...");\n'.replace(
                    "{{ component.name }}", component.name
                ),
                dry_run, force,
            )
            safe_write(
                comp_path / "tests" / "index.test.ts",
                "test('basic', () => {\n  expect(true).toBe(true);\n});\n",
                dry_run, force,
            )
        elif lang == "python":
            safe_write(
                comp_path / "src" / "main.py",
                f'print("Starting {component.name}...")\n',
                dry_run, force,
            )
            safe_write(
                comp_path / "tests" / "test_main.py",
                "def test_basic():\n    assert True\n",
                dry_run, force,
            )
        else:
            safe_write(comp_path / "src" / ".gitkeep", "", dry_run, force)
            safe_write(comp_path / "tests" / ".gitkeep", "", dry_run, force)

        # Standard run scripts
        scripts = ["run.sh", "test.sh", "docker-build.sh", "docker-run.sh"]
        for script in scripts:
            spath = comp_path / "scripts" / script
            safe_write(
                spath,
                self.renderer.render(f"repository/scripts/{script}.j2", comp_context),
                dry_run, force,
            )
            make_executable(spath, dry_run)

        # Database migrations (only for components that own a database)
        if component.database != "none":
            safe_mkdir(comp_path / "migrations", dry_run)
            safe_write(
                comp_path / "migrations" / "README.md",
                self.renderer.render("repository/migrations/README.md.j2", comp_context),
                dry_run, force,
            )
            safe_write(
                comp_path / "docs" / "DATABASE.md",
                self.renderer.render("repository/docs/DATABASE.md.j2", comp_context),
                dry_run, force,
            )
            db_scripts = ["migrate-up.sh", "migrate-info.sh", "migrate-clean-local.sh"]
            for script in db_scripts:
                spath = comp_path / "scripts" / script
                safe_write(
                    spath,
                    self.renderer.render(f"repository/scripts/{script}.j2", comp_context),
                    dry_run, force,
                )
                make_executable(spath, dry_run)
