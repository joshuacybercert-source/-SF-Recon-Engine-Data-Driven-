#!/usr/bin/env python3
"""SF Parcel-Event Reconciliation - Main entry point.

Loads San Francisco parcels, matches events from city datasets,
and outputs event counts per parcel.
"""

import argparse
import logging
import sys

from engine.parcels import load_parcels
from engine.events import match_events


def setup_logging(verbose: bool = False) -> None:
    """Configure application logging."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


def main() -> int:
    """Run reconciliation and print results."""
    parser = argparse.ArgumentParser(
        description="SF Parcel-Event Reconciliation",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable debug logging",
    )
    parser.add_argument(
        "-n", "--top",
        type=int,
        default=20,
        help="Number of top parcels to display (default: 20)",
    )
    args = parser.parse_args()

    setup_logging(verbose=args.verbose)

    parcels = load_parcels()
    if not parcels:
        logging.error("No parcels loaded. Exiting.")
        return 1

    counts = match_events(parcels)
    total = sum(counts.values())

    print(f"\nReconciliation complete: {total} events across {len(counts)} parcels\n")
    print("Top parcels by event count:")
    print("-" * 40)
    for key, count in counts.most_common(args.top):
        print(f"  {key}: {count}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
