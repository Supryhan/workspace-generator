# ADR 0001: Use Workspace Instead of Platform

Status: accepted  
Date: 2026-06-02

## Context

The project was initially developed under the name `platform-generator` and used the term `platform` as the primary architectural concept.

During early development, this terminology became confusing. The generated structure looked as if one platform contained other platforms or platform-like repositories. This made the conceptual model unclear.

The intended purpose of the tool is not to generate a large abstract platform. The tool generates a local working structure that groups related repositories, infrastructure, documentation, and components for a specific solution or product.

Examples include:

- `student-management`
- `product-catalog`
- `wallet`
- `order-management`

Each generated structure should act as a local development workspace for a concrete solution.

## Decision

The project will use the term `workspace` as the primary generated structure.

The canonical package name is:

```text
workspace_generator
```

The canonical CLI command is:

```text
workspace-generator
```

The default output directory is:

```text
~/DEVELOPER/workspaces
```

The generated root structure is a workspace, not a platform.

Example:

```text
~/DEVELOPER/workspaces/product-catalog/
├── index/
├── infra/
├── services/
├── apps/
├── jobs/
├── connectors/
└── libraries/
```

The term `solution` may be used to describe the logical business or product system implemented inside a workspace.

The term `component` may remain as an internal umbrella concept in the configuration and implementation, but generated folders should be grouped by role:

```text
services/
apps/
jobs/
connectors/
libraries/
```

The old terms `platform-generator`, `platform_generator`, `PlatformGenerator`, and `PlatformMeta` are not part of the canonical project model.

## Consequences

This decision makes the project terminology clearer.

A workspace is easier to understand as a local development container that holds related repositories and infrastructure.

The generated structure becomes more natural:

- `index/` describes the workspace;
- `infra/` contains infrastructure assets;
- `services/` contains backend services;
- `apps/` contains user-facing applications;
- `jobs/` contains background or batch jobs;
- `connectors/` contains integration components;
- `libraries/` contains shared code.

This terminology also reduces confusion between generated repositories and the higher-level structure that contains them.

The cost of this decision is that all old platform-related names must be migrated or removed. This includes package names, class names, templates, tests, blueprints, documentation, and generated text.

## Alternatives Considered

### Keep Platform

The term `platform` was considered too broad and potentially misleading. It suggested that the tool generated a full software platform rather than a structured local development workspace.

### Use Solution as the Root Concept

The term `solution` is useful, but it describes the logical business system rather than the local filesystem structure. A solution may live inside a workspace, but it is not the best name for the generated root directory.

### Use Project

The term `project` is too overloaded. It may refer to a GitHub repository, an IDE project, a business initiative, or a generated component. Using `project` as the main concept would create ambiguity.

## Final Decision

Use `workspace` as the root generated structure and `solution` as the logical business/product concept inside the workspace.
