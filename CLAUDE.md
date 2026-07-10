# CLAUDE.md

# Project Operating Instructions

This repository follows a documentation-first development workflow.

The primary source of truth for the project is:

> design.md

`design.md` is the authoritative engineering context document and should always reflect the current state of the project.

When information already exists in `design.md`, treat it as the canonical source rather than rediscovering it by inspecting the repository.

---

# Primary Rules

Before responding to any engineering request:

1. Consult `design.md`.
2. Determine the current project state.
3. Treat documented decisions as authoritative unless explicitly told otherwise.
4. Use `design.md` as the project's persistent engineering memory.
5. Only inspect the repository when:
   - information is missing,
   - the user explicitly requests an audit,
   - the documentation appears inconsistent,
   - or repository validation is required.

---

# Development Workflow

## Before Starting Any Work

Before implementing any feature or modification:

- Review the relevant sections of `design.md`.
- Identify the current phase.
- Identify the active milestone.
- Review pending tasks.
- Identify dependencies.
- Determine whether the requested work belongs in the current roadmap.

If the request belongs to a future milestone, explain why before proceeding.

---

## Beginning a New Phase

When beginning a new project phase, update `design.md` with:

- Current Phase
- Current Milestone
- Objectives
- Planned Deliverables
- Expected Repository Changes
- Dependencies
- Risks

Do this before implementation whenever repository editing is available.

---

## During Development

Whenever repository editing is available, update `design.md` alongside the code whenever you:

- create files
- delete files
- rename files
- move files
- refactor modules
- reorganize folders
- introduce dependencies
- remove dependencies
- add libraries
- modify environment variables
- introduce external services
- change architecture
- make significant engineering decisions
- complete milestones

Documentation should evolve together with the implementation.

Never postpone documentation until the end of development.

If repository editing is unavailable, provide the required `design.md` updates as part of your response.

---

# Development Log

After completing meaningful work, append a new Development Log entry containing:

- Timestamp (logical project time)
- Task completed
- Files created
- Files modified
- Files deleted
- Reason for change
- Architectural decisions
- Remaining work
- Known issues
- Recommended next task

Never overwrite previous entries.

Always append.

---

# Required Sections in design.md

The document should contain, where applicable:

1. Project Overview
2. Architecture
3. Repository Structure
4. Technology Stack
5. Design Decisions (DD-001, DD-002, ...)
6. Dependencies
7. Environment Variables
8. External Integrations
9. Infrastructure & Deployment
10. Domain-Specific Components
11. Current Phase
12. Current Milestone
13. Completed Milestones
14. Pending Tasks
15. Known Issues
16. Technical Debt
17. Future Improvements
18. Development Log
19. Current Repository State

Projects may add additional sections when appropriate.

---

# Updating Existing Information

Never recreate information already documented.

Instead:

- Update it
- Extend it
- Revise it

Preserve historical context whenever practical.

Treat `design.md` as a living engineering wiki rather than a generated report.

---

# End of Every Response

When repository editing is available:

1. Update `design.md`.
2. Summarize the sections updated.
3. Confirm that `design.md` reflects the latest project state.

When repository editing is unavailable:

1. Describe the required `design.md` changes.
2. List the affected sections.

---

# Engineering Standards

Prefer:

- Production-quality implementations
- Modular architecture
- SOLID principles
- Clean code
- High cohesion
- Low coupling
- Reusable components
- Scalable folder structures
- Explicit documentation
- Maintainable abstractions
- Strong typing where appropriate
- Automated testing where appropriate
- Consistent linting and formatting

Avoid:

- Duplicate code
- Temporary hacks
- Magic numbers
- Hidden dependencies
- Monolithic modules
- Premature optimization
- Unnecessary complexity
- Dead code
- Inconsistent naming
- Untracked architectural decisions

---

# Repository Audits

Repository-wide audits are expensive.

Only perform one when:

- explicitly requested,
- `design.md` is missing,
- documentation appears inconsistent,
- significant refactoring requires validation,
- or repository integrity needs verification.

Otherwise, trust `design.md`.

---

# Goal

A new engineer should be able to understand:

- what the project is,
- why it exists,
- how it is structured,
- what decisions have been made,
- where development currently stands,
- what remains to be built,
- and how to continue development,

by reading only `design.md`, without needing to inspect the repository.