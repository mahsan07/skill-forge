# Skill Forge

Author, validate, and test focused SKILL.md packages.

## Why this exists

Reusable agent skills become unreliable when their triggers are vague, instructions are bloated, or safety and validation are missing.

## What it provides

Provide templates, validators, examples, quality checks, and fixture-based benchmark tooling for small agent skills that expose a clear workflow.

## Intended users

Agent builders creating portable skills for Hermes, Codex, or compatible skill systems.

## Example

Create and validate a skill that performs evidence-first exploratory QA on a web app.

## Token-compression benchmark

Skill Forge includes a task-adaptive benchmark for comparing real installed context/response compressors without reimplementing them.

It measures before/after size, provider-neutral estimated token units, latency, and exact retention of critical facts. A smaller result fails when a required constraint, command, number, path, or other marked fact disappears.

See [benchmarks/token-compression](benchmarks/token-compression/README.md).

## Visual overview

![Skill Forge architecture flow](assets/architecture-flow.svg)

[Open the architecture and sequence diagrams](docs/DIAGRAMS.md).

## Current status

Runnable local MVP with skill generation/validation plus an experimental token-compression adapter benchmark.

## Documentation

- [Product definition](docs/PRODUCT.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Flow and sequence diagrams](docs/DIAGRAMS.md)
- [Safety](docs/SAFETY.md)
- [Roadmap](docs/ROADMAP.md)

## License

MIT. See [LICENSE](LICENSE).
