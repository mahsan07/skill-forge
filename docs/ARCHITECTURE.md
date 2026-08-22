# Architecture

## Design summary

A CLI creates a skill folder, validates metadata, and optionally runs deterministic checks. The skill itself remains plain Markdown plus optional scripts and references.

## Main components

- Define concrete trigger examples
- Choose a focused scope
- Generate valid metadata
- Write the minimum reliable workflow
- Validate and forward-test

## Initial implementation boundary

Start with a local, inspectable implementation. Prefer plain files, small typed schemas, and deterministic commands before introducing a database, hosted service, or provider-specific adapter.

## Verification

Every MVP feature should have at least one fixture, one failure case, and one visible verification artifact. Keep inferred behavior separate from measured behavior.
