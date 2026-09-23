from __future__ import annotations

import argparse
import json
from pathlib import Path

from .forge import create_skill, inspect_skill
from .token_benchmark import run_benchmark_files


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="skill-forge")
    commands = root.add_subparsers(dest="command", required=True)
    init = commands.add_parser("init", help="create a minimal skill package")
    init.add_argument("name")
    init.add_argument("--path", default=".")
    init.add_argument("--description", required=True)
    init.add_argument("--display-name")
    init.add_argument("--short-description")
    init.add_argument("--resources", default="", help="comma-separated: scripts,references,assets")
    validate = commands.add_parser("validate", help="validate metadata, structure, and public safety")
    validate.add_argument("skill_dir")
    rubric = commands.add_parser("rubric", help="show the quality score and findings")
    rubric.add_argument("skill_dir")
    benchmark = commands.add_parser("benchmark-tokens", help="compare token-compression adapters on shared fixtures")
    benchmark.add_argument("--fixtures", required=True)
    benchmark.add_argument("--adapters", required=True)
    benchmark.add_argument("--output", help="optional JSON report path")
    return root


def main(argv: list[str] | None = None) -> int:
    root = parser()
    args = root.parse_args(argv)
    try:
        if args.command == "init":
            resources = tuple(part.strip() for part in args.resources.split(",") if part.strip())
            path = create_skill(args.path, args.name, args.description, display_name=args.display_name,
                                short_description=args.short_description, resources=resources)
            output = {"created": str(path), "next": f"Edit {path / 'SKILL.md'}, then run skill-forge validate {path}"}
            code = 0
        elif args.command == "benchmark-tokens":
            output = run_benchmark_files(args.fixtures, args.adapters)
            if args.output:
                Path(args.output).write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            code = 0 if all(item["failures"] == 0 for item in output["summary"].values()) else 1
        else:
            output = inspect_skill(args.skill_dir)
            code = 0 if output["valid"] else 1
    except (ValueError, FileExistsError, OSError) as error:
        root.error(str(error))
    print(json.dumps(output, indent=2, sort_keys=True))
    return code
