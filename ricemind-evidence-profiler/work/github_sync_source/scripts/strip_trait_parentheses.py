#!/usr/bin/env python
"""Remove one pair of outer parentheses from each line in a traits file."""

from __future__ import annotations

import argparse
from pathlib import Path


DEFAULT_INPUT = Path(__file__).resolve().parent.parent / "references" / "All-Traits.txt"


def strip_outer_parentheses(path: Path) -> tuple[int, int]:
    lines = path.read_text(encoding="utf-8-sig").splitlines()
    output: list[str] = []
    changed = 0

    for line in lines:
        if line.startswith("(") and line.endswith(")"):
            line = line[1:-1]
            changed += 1
        output.append(line)

    newline = "\n" if lines else ""
    path.write_text("\n".join(output) + newline, encoding="utf-8")
    return len(lines), changed


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Remove the first '(' and final ')' from each wrapped line."
    )
    parser.add_argument(
        "path",
        nargs="?",
        type=Path,
        default=DEFAULT_INPUT,
        help=f"file to update (default: {DEFAULT_INPUT})",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    path = args.path.resolve()
    if not path.is_file():
        raise SystemExit(f"File not found: {path}")

    total, changed = strip_outer_parentheses(path)
    print(f"Processed {total} lines; removed parentheses from {changed} lines: {path}")


if __name__ == "__main__":
    main()
