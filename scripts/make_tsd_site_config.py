#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a site-specific TSD wrapper config from the checked-in template.",
    )
    parser.add_argument("--username", required=True, help="TSD username, for example p33-ofrei")
    parser.add_argument("--output", required=True, help="Output YAML path, for example ~/nvflare_wrapper_demo/tsd-configs/p33.yml")
    parser.add_argument(
        "--template",
        default="examples/hello_regression/tsd_wrapper_config.yml.template",
        help="Template YAML path",
    )
    parser.add_argument("--force", action="store_true", help="Overwrite an existing output file")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    template_path = Path(args.template).expanduser()
    output_path = Path(args.output).expanduser()

    if not template_path.exists():
        raise FileNotFoundError(f"Template not found: {template_path}")
    if output_path.exists() and not args.force:
        raise FileExistsError(f"Output already exists: {output_path}. Use --force to overwrite.")

    lines = template_path.read_text(encoding="utf-8").splitlines()
    rendered = []
    replaced = False
    for line in lines:
        if line.startswith("username:"):
            rendered.append(f"username: {args.username}")
            replaced = True
        else:
            rendered.append(line)
    if not replaced:
        raise RuntimeError(f"Template missing username field: {template_path}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(rendered) + "\n", encoding="utf-8")
    print(f"Wrote {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
