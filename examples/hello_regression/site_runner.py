#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

from common import compute_local_statistics


def main():
    parser = argparse.ArgumentParser(description="Generate local synthetic regression statistics.")
    parser.add_argument("--site-name", required=True, help="NVFlare site name.")
    parser.add_argument("--output", required=True, help="Path to output JSON file.")
    args = parser.parse_args()

    payload = compute_local_statistics(args.site_name)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2))
    print(f"Wrote local statistics for {args.site_name} to {output_path}")


if __name__ == "__main__":
    main()
