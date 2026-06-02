# workspace-generator

Python CLI tool for generating structured, git-ready local workspaces from YAML blueprints.

All workspaces and generated components reside under the user home directory in a fully uppercase directory named `DEVELOPER` by default:

```text
~/DEVELOPER/
├── workspace-generator/    # This generator tool repository
└── workspaces/             # Generated local workspaces
```

---

## Terminology

* **workspace**: The local container directory grouping all associated repositories, configuration files, and tools for a specific project.
* **solution**: The logical collection of services, apps, and libraries that address a unified business domain (e.g., student management).
* **repository**: A physical Git repository or sub-directory within the workspace, mapped to a relative local path and an upstream remote.
* **service**: A backend API or web service (e.g., Scala http4s service, microservice).
* **app**: A client-facing application or user interface (e.g., React web frontend, mobile client).
* **job**: A batch processing script, task runner, or offline worker (e.g., Apache Spark data pipeline).
* **connector**: An integration component connecting the system to external services or message queues (e.g., Kafka source/sink event connector).
* **library**: A shared code dependency, model package, or utility module (e.g., common domain models).

---

## Workspace Structure

By default, generated workspaces are outputted to the base directory:
`~/DEVELOPER/workspaces`

For a workspace configured via a blueprint, the expected generated structure organizes repositories neatly without workspace-prefixing local folders:

```text
~/DEVELOPER/workspaces/<workspace-name>/
├── index/                  # Central metadata index repository
├── infra/                  # Shared infrastructure configuration and Compose scaffolds
├── services/               # Directory containing all backend service repositories
│   └── students-service/
├── apps/                   # Directory containing frontend application repositories
│   └── web-frontend/
├── jobs/                   # Directory containing batch processing repositories
│   └── analytics-spark-job/
├── connectors/             # Directory containing integration connector repositories
│   └── kafka-events-connector/
└── libraries/              # Directory containing shared library repositories
    └── shared-domain/
```

> [!NOTE]
> Local folder names (e.g., `services/students-service`) are not prefixed with the workspace name. However, their upstream remote repository names (e.g., `student-management-students-service`) may be prefixed.

---

## Installation & Setup

Ensure you have Python 3.10+ installed.

1. Navigate to the directory:
   ```bash
   cd ~/DEVELOPER/workspace-generator
   ```

2. Install dependencies:
   ```bash
   pip install -e .
   # Or using uv:
   uv pip install -e .
   ```

---

## CLI Usage

Generate a workspace using the CLI tool:

```bash
python -m workspace_generator create --config blueprints/student-management.example.yaml
```

### Dry-Run Usage

To simulate generation and preview the directories/files that would be created without modifying the disk:

```bash
python -m workspace_generator create --config blueprints/student-management.example.yaml --dry-run
```

### Safety Flags

* `--dry-run`: Runs full parsing and blueprint validation, printing simulated folder structures without writing directories.
* `--force`: Forcefully overwrites any existing workspace folders or component subdirectories.
* `--skip-existing`: Safely skips generating component folders that already exist, while constructing any new ones.
* `--fail-if-exists` (Default): Halts execution if the target workspace folder or any constituent component directory already exists.
* `--base-dir <path>`: Overrides the default base output directory from `~/DEVELOPER/workspaces`.

---

## YAML Blueprint Schema

Workspaces are defined using a structured YAML blueprint. The schema includes configuration for the workspace, the solution, and specific components:

```yaml
workspace:
  name: student-management
  display_name: Student Management Workspace
  base_directory: ~/DEVELOPER/workspaces
  github_owner: your-github-owner
  default_visibility: private
  repository_mode: starter

solution:
  name: student-management
  display_name: Student Management System
  domain: education

environments:
  - local
  - DEV
  - SIT
  - UAT
  - PROD

repositories:
  index:
    enabled: true
    path: index
  infra:
    enabled: true
    path: infra

components:
  - name: students-service
    kind: service  # Allowed kinds: service | app | job | connector | library
    repository:
      path: services/students-service
      remote_name: student-management-students-service
    language: scala
    framework: http4s
    database: postgres
    port: 8081
    version: 0.3.1
```

---

## Verification & Testing

Verify that all unit tests run and pass using pytest:

```bash
python3 -m pytest tests/ -v
```
