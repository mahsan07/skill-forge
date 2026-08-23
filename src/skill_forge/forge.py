"""Create and inspect compact, portable agent skill packages."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

NAME_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SUSPICIOUS_PATTERNS = {
    "credential assignment": re.compile(r"(?i)(api[_-]?key|token|password|secret)\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{12,}"),
    "private key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "local home path": re.compile(r"(?i)(?:C:\\Users\\[^\\\s]+|/Users/[^/\s]+|/home/[^/\s]+)"),
    "private network address": re.compile(r"(?i)https?://(?:localhost|127\.0\.0\.1|10\.\d+\.\d+\.\d+|192\.168\.\d+\.\d+)"),
}


def create_skill(
    output: str | Path,
    name: str,
    description: str,
    *,
    display_name: str | None = None,
    short_description: str | None = None,
    resources: tuple[str, ...] = (),
) -> Path:
    errors = validate_name(name)
    if errors:
        raise ValueError("; ".join(errors))
    if not description.strip() or "\n" in description or "\r" in description:
        raise ValueError("description must be a non-empty single line")
    for resource in resources:
        if resource not in {"scripts", "references", "assets"}:
            raise ValueError(f"unsupported resource directory: {resource}")
    title = display_name or " ".join(part.capitalize() for part in name.split("-"))
    short = short_description or f"Run the focused {title} workflow"
    if not 25 <= len(short) <= 64:
        raise ValueError("short_description must contain 25 to 64 characters")
    skill_dir = Path(output) / name
    if skill_dir.exists():
        raise FileExistsError(f"refusing to overwrite existing skill: {skill_dir}")
    skill_dir.mkdir(parents=True)
    for resource in resources:
        (skill_dir / resource).mkdir()
    skill_md = f'''---
name: {name}
description: "{yaml_string(description)}"
---

# {title}

## Workflow

1. Confirm the requested outcome and inputs.
2. Perform the focused workflow using only the provided scope.
3. Validate the result before reporting completion.

## Output

Return the result, validation evidence, and any unresolved limitations.
'''
    (skill_dir / "SKILL.md").write_text(skill_md, encoding="utf-8")
    agents = skill_dir / "agents"
    agents.mkdir()
    openai_yaml = f'''interface:
  display_name: "{yaml_string(title)}"
  short_description: "{yaml_string(short)}"
  default_prompt: "Use ${name} to complete this task and validate the result."
'''
    (agents / "openai.yaml").write_text(openai_yaml, encoding="utf-8")
    return skill_dir


def inspect_skill(skill_dir: str | Path) -> dict[str, Any]:
    root = Path(skill_dir)
    errors: list[str] = []
    warnings: list[str] = []
    skill_path = root / "SKILL.md"
    if not skill_path.exists():
        return {"valid": False, "score": 0, "errors": ["SKILL.md is missing"], "warnings": [], "public_scrub": []}
    text = skill_path.read_text(encoding="utf-8")
    metadata, body, frontmatter_errors = parse_frontmatter(text)
    errors.extend(frontmatter_errors)
    name = metadata.get("name", "")
    description = metadata.get("description", "")
    errors.extend(validate_name(name))
    if name and root.name != name:
        errors.append(f"folder name '{root.name}' must match skill name '{name}'")
    if not description:
        errors.append("description is required")
    elif len(description) > 1024:
        errors.append("description must be at most 1024 characters")
    elif not re.search(r"(?i)\b(use|when|for|whenever)\b", description):
        warnings.append("description should state when the skill should trigger")
    if len(body.splitlines()) > 500:
        errors.append("SKILL.md body must stay under 500 lines")
    if re.search(r"(?i)\b(TODO|FIXME|placeholder)\b", text):
        errors.append("remove TODO, FIXME, or placeholder text")
    if "## when to use" in body.lower():
        warnings.append("put trigger guidance in frontmatter description, not the body")
    ui = root / "agents" / "openai.yaml"
    if not ui.exists():
        warnings.append("agents/openai.yaml is recommended")
    elif name and f"${name}" not in ui.read_text(encoding="utf-8"):
        errors.append("agents/openai.yaml default_prompt must mention the skill as $skill-name")
    scrub = public_scrub(root)
    errors.extend(f"public scrub: {finding}" for finding in scrub)
    score = 100
    score -= 15 * len(errors)
    score -= 5 * len(warnings)
    score = max(0, score)
    return {"valid": not errors, "score": score, "errors": errors, "warnings": warnings, "public_scrub": scrub}


def parse_frontmatter(text: str) -> tuple[dict[str, str], str, list[str]]:
    if not text.startswith("---\n"):
        return {}, text, ["SKILL.md must start with YAML frontmatter"]
    try:
        frontmatter, body = text[4:].split("\n---\n", 1)
    except ValueError:
        return {}, text, ["SKILL.md frontmatter is not closed"]
    metadata: dict[str, str] = {}
    errors: list[str] = []
    for line in frontmatter.splitlines():
        if ":" not in line:
            errors.append(f"invalid frontmatter line: {line}")
            continue
        key, value = line.split(":", 1)
        key, value = key.strip(), value.strip().strip('"').strip("'")
        if key in metadata:
            errors.append(f"duplicate frontmatter key: {key}")
        metadata[key] = value
    extras = set(metadata) - {"name", "description"}
    if extras:
        errors.append(f"frontmatter supports only name and description; found: {', '.join(sorted(extras))}")
    for required in ("name", "description"):
        if required not in metadata:
            errors.append(f"frontmatter is missing {required}")
    return metadata, body, errors


def validate_name(name: str) -> list[str]:
    errors = []
    if not name:
        return ["name is required"]
    if len(name) > 64:
        errors.append("name must be at most 64 characters")
    if not NAME_PATTERN.fullmatch(name):
        errors.append("name must use lowercase letters, digits, and single hyphens")
    return errors


def public_scrub(root: Path) -> list[str]:
    findings = []
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".webp", ".pdf"}:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for label, pattern in SUSPICIOUS_PATTERNS.items():
            if pattern.search(text):
                findings.append(f"{path.relative_to(root)} contains a possible {label}")
    return findings


def yaml_string(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ")
