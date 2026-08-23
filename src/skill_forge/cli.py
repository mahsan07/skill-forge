from __future__ import annotations

import argparse
import json

from .forge import create_skill, inspect_skill


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
        else:
            output = inspect_skill(args.skill_dir)
            code = 0 if output["valid"] else 1
    except (ValueError, FileExistsError, OSError) as error:
        root.error(str(error))
    print(json.dumps(output, indent=2, sort_keys=True))
    return code
