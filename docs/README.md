# Project Documentation

This directory contains project-level documentation for `workspace-generator`.

The documentation is divided into two main areas:

- `plans/` — planned features, implementation ideas, enhancement proposals, and future development notes.
- `adr/` — Architecture Decision Records that document important architectural decisions made in the project.

## Purpose

The goal of this documentation structure is to keep the project maintainable as it grows.

Not every idea should immediately become source code. Some ideas need to be captured first, reviewed later, refined into implementation plans, and only then developed in a feature branch.

## Directory Structure

```text
docs/
├── README.md
├── plans/
│   └── README.md
└── adr/
    └── README.md
```

## Documentation Types

### Plans

Plans describe future or current implementation ideas. A plan may describe a feature that is not implemented yet, a planned enhancement, or a task that requires further analysis.

Plans are not necessarily final architectural decisions.

### ADRs

Architecture Decision Records document accepted architectural decisions.

An ADR should explain the context, the decision, the consequences, and the alternatives considered.

## Naming Convention

Use numbered filenames to preserve chronological order.

Recommended format:

```text
0001-short-topic-name.md
0002-another-topic-name.md
```

Examples:

```text
docs/plans/0001-workspace-preview-tree.md
docs/adr/0001-use-workspace-instead-of-platform.md
```
