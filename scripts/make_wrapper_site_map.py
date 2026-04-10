#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a simulation site map for tutorial 3 wrapper clients.",
    )
    parser.add_argument("--output", required=True, help="Output JSON path")
    parser.add_argument("--p33-config", default="", help="Path to p33 TSD config")
    parser.add_argument("--p697-config", default="", help="Path to p697 TSD config")
    parser.add_argument("--dx-config", default="", help="Path to ukb-rap DX config")
    return parser.parse_args()


def add_entry(site_map: dict[str, dict], logical_site: str, executor: str, env_key: str, config_path: str) -> None:
    if not config_path:
        return
    resolved_config = Path(config_path).expanduser()
    if not resolved_config.exists():
        return
    sim_site_name = f"site-{len(site_map) + 1}"
    site_map[sim_site_name] = {
        "site_name": logical_site,
        "executor": executor,
        "env": {
            env_key: str(resolved_config.resolve()),
        },
    }


def main() -> int:
    args = parse_args()
    site_map: dict[str, dict] = {}
    add_entry(site_map, "p33", "tsd", "HELLO_REGRESSION_TSD_CONFIG", args.p33_config)
    add_entry(site_map, "p697", "tsd", "HELLO_REGRESSION_TSD_CONFIG", args.p697_config)
    add_entry(site_map, "ukb-rap", "dx", "HELLO_REGRESSION_DX_CONFIG", args.dx_config)

    output_path = Path(args.output).expanduser()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(site_map, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
