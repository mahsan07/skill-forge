# Safety and Trust Boundaries

This project is designed to be useful without silently taking control of external systems.

## Required boundaries

- Keep credentials and personal data out of packages
- Put all trigger conditions in metadata
- Do not hide critical safety rules in optional references
- Validate before sharing
- Avoid provider-specific claims unless tested

## Default posture

- Read-only and dry-run modes come first.
- Human approval is required for external communication, spending, publication, destructive changes, access changes, and merges.
- Logs and examples must not contain secrets, private endpoints, personal identifiers, or private source material.
- Every side effect must be attributable to an explicit request and a verifiable execution record.
