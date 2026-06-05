#!/usr/bin/env python3
"""Lint a pull request body against AI Issue-to-Production process rules.

The lint enforces the company release governance contract on every PR:

- The body must reference an issue with ``Refs #<number>``.
- The body must not use GitHub auto-close keywords (``Closes``/``Fixes``/
  ``Resolves``) that would close the issue on merge.
- The body must contain the required handoff sections so reviewers and the
  deploy operator have verification, deploy impact, and rollback context.

Usage:
    python scripts/ai_process_lint.py --body-file pr_body.txt
    PR_BODY="$(cat pr_body.txt)" python scripts/ai_process_lint.py
"""

from __future__ import annotations

import argparse
import os
import re
import sys


REFS_PATTERN = re.compile(r"Refs\s+#\d+", re.IGNORECASE)
AUTO_CLOSE_PATTERN = re.compile(
    r"\b(close[sd]?|fix(e[sd])?|resolve[sd]?)\b\s+#\d+",
    re.IGNORECASE,
)
REQUIRED_SECTIONS = ("摘要", "变更范围", "验证", "部署影响", "回滚")


def lint(body: str) -> list[str]:
    errors: list[str] = []

    if not REFS_PATTERN.search(body):
        errors.append("PR body must reference an issue with `Refs #<number>`.")

    if AUTO_CLOSE_PATTERN.search(body):
        errors.append(
            "PR body must not use auto-close keywords "
            "(Closes/Fixes/Resolves); use `Refs #<number>` instead."
        )

    for section in REQUIRED_SECTIONS:
        if section not in body:
            errors.append(f"PR body is missing required section: {section}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--body-file",
        help="Path to a file containing the PR body. Falls back to PR_BODY env.",
    )
    args = parser.parse_args()

    if args.body_file:
        with open(args.body_file, encoding="utf-8") as handle:
            body = handle.read()
    else:
        body = os.environ.get("PR_BODY", "")

    if not body.strip():
        print("PR body is empty; cannot validate process rules.", file=sys.stderr)
        return 1

    errors = lint(body)
    if errors:
        print("AI process lint failed:", file=sys.stderr)
        for error in errors:
            print(f" - {error}", file=sys.stderr)
        return 1

    print("AI process lint passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
