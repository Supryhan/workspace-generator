# Implementation Plans

This directory contains implementation plans, feature ideas, enhancement proposals, and future development notes for `workspace-generator`.

## Purpose

Implementation plans are used to capture ideas before they are implemented.

A plan may describe:

- a future feature;
- a proposed improvement;
- a refactoring idea;
- a planned user experience enhancement;
- a technical task that should be implemented later;
- an AI-agent handoff plan for future development.

A plan does not necessarily mean that the feature is already implemented.

## Recommended Status Values

Each plan should include a status field near the top of the document.

Recommended statuses:

```text
Status: idea
Status: planned
Status: approved
Status: in-progress
Status: implemented
Status: superseded
Status: rejected
```

## Recommended Plan Structure

```markdown
# Plan 0001: Feature Name

Status: planned
Priority: medium
Created: YYYY-MM-DD

## Summary

Short explanation of the idea.

## Motivation

Why this feature or change is needed.

## Proposed Changes

What should be changed.

## Scope

What is included and what is not included.

## Implementation Notes

Technical notes for future implementation.

## Verification

Commands, tests, or manual checks that should confirm the feature works.

## Open Questions

Questions that should be resolved before or during implementation.
```

## Naming Convention

Use numbered filenames:

```text
0001-workspace-preview-tree.md
0002-api-contracts-and-qa-artifacts.md
0003-product-catalog-starter-code.md
```

The number reflects creation order, not permanent priority. Priority should be written inside the plan.
