---
name: evidence-first-qa
description: Inspect a local web application and report reproducible usability defects with screenshots and exact steps. Use when a user asks to test, audit, or perform exploratory QA on a web interface.
---

# Evidence First QA

## Workflow

1. Confirm the application URL and the user journey in scope.
2. Capture the initial state before interacting.
3. Exercise the journey without modifying production data.
4. Record each defect with exact steps, expected behavior, observed behavior, and evidence.
5. Re-run the highest-impact findings to confirm reproducibility.

## Output

Return a severity-ordered defect list, evidence locations, tested scope, and untested limitations.
