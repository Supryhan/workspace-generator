import argparse
import sys
from pathlib import Path
from workspace_generator.generator import WorkspaceGenerator


def main():
    parser = argparse.ArgumentParser(
        description="workspace-generator: Generate structured local workspaces from YAML blueprints."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    create_parser = subparsers.add_parser(
        "create",
        help="Create a workspace from a YAML blueprint.",
    )
    create_parser.add_argument(
        "--config",
        required=True,
        help="Path to the workspace YAML blueprint file.",
    )

    # Mutually exclusive safety mode flags
    group = create_parser.add_mutually_exclusive_group()
    group.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate generation without writing any directories or files to disk.",
    )
    group.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing workspace and repository folders.",
    )
    group.add_argument(
        "--skip-existing",
        action="store_true",
        help="Skip repository folders that already exist; only write missing ones.",
    )
    group.add_argument(
        "--fail-if-exists",
        action="store_true",
        help="Halt execution if any target workspace folders already exist (Default).",
    )

    create_parser.add_argument(
        "--base-dir",
        help="Override the workspaces base output directory (Default: ~/DEVELOPER/workspaces).",
    )

    args = parser.parse_args()

    if args.command == "create":
        if args.dry_run:
            safety_mode = "dry-run"
        elif args.force:
            safety_mode = "force"
        elif args.skip_existing:
            safety_mode = "skip-existing"
        else:
            safety_mode = "fail-if-exists"

        try:
            generator = WorkspaceGenerator(
                safety_mode=safety_mode,
                base_dir_override=args.base_dir,
            )
            generator.generate(args.config)
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
