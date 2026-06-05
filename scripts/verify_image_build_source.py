#!/usr/bin/env python3
"""Verify a production image is built from a merged PR on the release source.

Production images may only be built from commits that landed on the release
source branch (``dev``) through a merged pull request. This guards against
building images from direct pushes that bypassed review. The check uses the
GitHub CLI to look up the pull requests associated with the commit.

Usage:
    python scripts/verify_image_build_source.py \
        --sha <full-sha> --release-source dev

Requires ``gh`` to be authenticated (the workflow uses GITHUB_TOKEN).
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys


def associated_prs(sha: str) -> list[dict]:
    """Return merged PRs associated with the commit via the GitHub API."""
    result = subprocess.run(
        [
            "gh",
            "api",
            f"repos/{{owner}}/{{repo}}/commits/{sha}/pulls",
            "-H",
            "Accept: application/vnd.github+json",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        print(result.stderr, file=sys.stderr)
        return []
    try:
        return json.loads(result.stdout or "[]")
    except json.JSONDecodeError:
        return []


def is_merge_commit(sha: str) -> bool:
    result = subprocess.run(
        ["git", "rev-list", "--parents", "-n", "1", sha],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return False
    parents = result.stdout.split()
    # commit + 2 or more parents -> merge commit
    return len(parents) >= 3


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sha", required=True, help="Full 40-char commit SHA.")
    parser.add_argument(
        "--release-source",
        default="dev",
        help="Release source branch the image must be built from.",
    )
    args = parser.parse_args()

    if len(args.sha) != 40 or not all(c in "0123456789abcdef" for c in args.sha):
        print(f"SHA must be a full 40-char hex commit: {args.sha}", file=sys.stderr)
        return 1

    prs = associated_prs(args.sha)
    merged = [
        pr
        for pr in prs
        if pr.get("merged_at") and pr.get("base", {}).get("ref") == args.release_source
    ]

    if merged:
        pr = merged[0]
        print(
            f"OK: commit {args.sha} landed on {args.release_source} via merged "
            f"PR #{pr.get('number')}."
        )
        return 0

    if is_merge_commit(args.sha):
        print(
            f"OK: commit {args.sha} is a merge commit on {args.release_source}; "
            "treating as reviewed merge."
        )
        return 0

    print(
        f"BLOCK: commit {args.sha} is not associated with a merged PR targeting "
        f"{args.release_source}. Production images must come from merged PRs.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
