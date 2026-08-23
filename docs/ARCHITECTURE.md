# Architecture

```mermaid
flowchart TD
    C[skill-forge init] --> M[SKILL.md]
    C --> U[agents/openai.yaml]
    C -->|only when requested| R[scripts / references / assets]
    M --> P[Frontmatter parser]
    U --> P
    R --> P
    P --> N[Naming and structure checks]
    P --> G[Progressive-disclosure checks]
    P --> S[Public-scrub patterns]
    N --> O[JSON quality report]
    G --> O
    S --> O
```

## Design rules

- The generator refuses to overwrite an existing skill directory.
- Generated SKILL.md frontmatter contains only `name` and `description`.
- UI metadata is separate in `agents/openai.yaml` and quotes all strings.
- Optional resource directories exist only when requested.
- Validation returns machine-readable JSON and a process exit code.

The frontmatter parser intentionally supports the compact flat metadata used by portable skills; it is not a general YAML parser. Public-scrub patterns are explainable heuristics and may produce false positives or miss encoded secrets.

## Progressive disclosure

```text
metadata (always visible)
  -> SKILL.md workflow (loaded when triggered)
      -> scripts/references/assets (loaded or executed only as needed)
```
