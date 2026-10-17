"""Command-line access to the same config database, for tooling that runs
before or outside the HTTP service (the Makefile uses `profiles` to decide
which Compose profiles to start, design.md DD-047).

    python -m appconfig.cli show
    python -m appconfig.cli profiles
    python -m appconfig.cli set enablePhase2 true
"""

import argparse
import json
import os
import sys

from appconfig.schema import AppConfigUpdate, seed_config_from_env
from appconfig.store import ConfigStore

PHASE2_PROFILE = "phase2"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="appconfig")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("show", help="Print the current config as JSON")
    commands.add_parser("profiles", help="Print the Compose profiles the config implies")
    set_cmd = commands.add_parser("set", help="Set one setting (camelCase name, JSON value)")
    set_cmd.add_argument("key")
    set_cmd.add_argument("value")
    args = parser.parse_args(argv)

    store = ConfigStore(os.environ.get("DATABASE_PATH", ":memory:"), seed_config_from_env())
    try:
        if args.command == "show":
            print(store.get().model_dump_json(by_alias=True, indent=2))
        elif args.command == "profiles":
            print(PHASE2_PROFILE if store.get().enable_phase2 else "")
        else:
            try:
                value = json.loads(args.value)
            except json.JSONDecodeError:
                value = args.value
            updated = store.update(AppConfigUpdate.model_validate({args.key: value}))
            print(updated.model_dump_json(by_alias=True, indent=2))
    finally:
        store.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
