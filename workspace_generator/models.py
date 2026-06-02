from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class WorkspaceMeta(BaseModel):
    """
    Describes the local filesystem workspace container.
    A workspace is the root directory under ~/DEVELOPER/workspaces/<name>/.
    """
    name: str
    display_name: str
    base_directory: str = Field(default="~/DEVELOPER/workspaces")
    github_owner: str
    default_visibility: str = Field(default="private")
    repository_mode: str = Field(default="starter")

    @field_validator("repository_mode")
    @classmethod
    def validate_repository_mode(cls, v: str) -> str:
        allowed = {"starter", "empty", "template"}
        if v not in allowed:
            raise ValueError(f"repository_mode must be one of {allowed}, got '{v}'")
        return v


class SolutionMeta(BaseModel):
    """
    Describes the business/domain system represented by the workspace.
    A solution is the conceptual system — separate from the filesystem container.
    When omitted in the blueprint, the generator defaults to workspace values.
    """
    name: str
    display_name: str
    domain: Optional[str] = None


class IndexRepositoryConfig(BaseModel):
    """Configuration for the workspace index repository."""
    enabled: bool = True
    path: str = "index"


class InfraRepositoryConfig(BaseModel):
    """Configuration for the workspace infrastructure repository."""
    enabled: bool = True
    path: str = "infra"


class RepositoriesConfig(BaseModel):
    """Top-level repositories configuration block."""
    index: IndexRepositoryConfig = Field(default_factory=IndexRepositoryConfig)
    infra: InfraRepositoryConfig = Field(default_factory=InfraRepositoryConfig)


class ComponentRepositoryConfig(BaseModel):
    """
    Repository configuration for an individual component.
    - path: workspace-relative local filesystem path (e.g. services/students-service)
    - remote_name: GitHub remote repository name (may carry workspace/solution prefix)
    """
    path: str
    remote_name: Optional[str] = None


class ComponentConfig(BaseModel):
    """
    Describes a single component (service, app, job, connector, or library) in the workspace.
    'component' is the internal umbrella term; 'kind' determines the generated folder group.
    """
    name: str
    kind: str
    repository: ComponentRepositoryConfig
    language: Optional[str] = None
    framework: Optional[str] = None
    database: str = Field(default="none")
    port: Optional[int] = None
    version: str = Field(default="0.1.0")
    template: Optional[str] = None

    @field_validator("kind")
    @classmethod
    def validate_kind(cls, v: str) -> str:
        allowed = {"service", "app", "job", "connector", "library"}
        if v not in allowed:
            raise ValueError(f"Component kind must be one of {allowed}, got '{v}'")
        return v


class BlueprintConfig(BaseModel):
    """
    Top-level workspace blueprint configuration.
    Parsed from a YAML file and validated by Pydantic.
    """
    workspace: WorkspaceMeta
    solution: Optional[SolutionMeta] = None
    environments: List[str]
    repositories: RepositoriesConfig = Field(default_factory=RepositoriesConfig)
    components: List[ComponentConfig] = Field(default_factory=list)

    @field_validator("environments")
    @classmethod
    def validate_environments(cls, v: List[str]) -> List[str]:
        allowed = {"local", "DEV", "SIT", "UAT", "PROD"}
        for env in v:
            if env not in allowed:
                raise ValueError(f"Environment must be one of {allowed}, got '{env}'")
        return v

    def effective_solution(self) -> SolutionMeta:
        """
        Returns the solution metadata.
        Falls back to workspace name/display_name if solution is not defined in the blueprint.
        """
        if self.solution:
            return self.solution
        return SolutionMeta(
            name=self.workspace.name,
            display_name=self.workspace.display_name,
            domain=None,
        )
