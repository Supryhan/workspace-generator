# Architecture Decision Records

This directory contains Architecture Decision Records for `workspace-generator`.

## Purpose

An Architecture Decision Record documents an important architectural decision made in the project.

ADRs help explain why the project is designed in a particular way. This is especially useful when the project evolves over time and earlier context may be forgotten.

## What Should Become an ADR

Use an ADR for decisions such as:

- terminology changes;
- repository structure decisions;
- package architecture;
- generated workspace structure;
- configuration schema changes;
- infrastructure conventions;
- runtime state handling;
- compatibility decisions.

## Recommended ADR Structure

```markdown
# ADR 0001: Decision Title

Status: accepted
Date: YYYY-MM-DD

## Context

What problem or situation led to this decision.

## Decision

What decision was made.

## Consequences

What becomes easier, harder, or more constrained because of this decision.

## Alternatives Considered

Other options that were considered and why they were not selected.
```

## Status Values

Recommended statuses:

```text
proposed
accepted
superseded
rejected
deprecated
```

## Naming Convention

Use numbered filenames:

```text
0001-use-workspace-instead-of-platform.md
0002-group-repositories-by-role.md
0003-keep-runtime-state-out-of-generated-source.md
```

The number reflects the chronological order in which the decision was documented.
