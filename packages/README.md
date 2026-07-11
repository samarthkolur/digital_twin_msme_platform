# Packages

Shared TypeScript packages consumed by more than one app or service (e.g. a
future `@digital-cousin/types` package for state-object types shared between
`apps/dashboard` and `services/api`) live here, one subdirectory per package,
each with its own `package.json`.

`pnpm-workspace.yaml` already includes `packages/*` in its workspace glob.
Per DD-013 in [`design.md`](../design.md), this directory is currently empty
because only one TypeScript package (`apps/dashboard`) exists — a shared
package is worth creating once a second TypeScript consumer needs to reuse
code, not before.
