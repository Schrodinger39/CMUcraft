"""Command-line entry point for the small footprint pipeline.
Run from the repository root so default data paths resolve correctly."""

import argparse
import json
from pathlib import Path
from .geo import Region
from .osm import download
from .build import build


def main():
    """Parse the survey command, dispatch it, and report errors without synthetic fallback."""
    parser = argparse.ArgumentParser(
        description="CMUcraft: 1 block = 1 metre, EPSG:32617"
    )
    parser.add_argument("command", choices=["download", "build"])
    parser.add_argument("--source", type=Path, default=Path("data/raw/cmu.osm"))
    parser.add_argument("--output", type=Path, default=Path("artifacts"))
    parser.add_argument("--lon", type=float, default=-79.9442)
    parser.add_argument("--lat", type=float, default=40.4431)
    parser.add_argument("--size", type=int, default=256)
    args = parser.parse_args()
    region = Region(args.lon, args.lat, args.size)
    try:
        if args.command == "download":
            result = download(region, args.source)
        else:
            result = build(args.source, args.output, region)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except Exception as exc:
        parser.exit(1, f"CMUcraft failed: {exc}\nNo synthetic data substituted.\n")


if __name__ == "__main__":
    main()
