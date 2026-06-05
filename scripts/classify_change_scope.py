#!/usr/bin/env python3
"""Classify a set of changed paths into AI Issue-to-Production change scopes.

The classifier is shared by the PR check and image build workflows so that the
same rules decide whether a change is docs-only, process-only,
release-governance, runtime, or unknown. Runtime or unknown changes are the
only ones allowed to build production images.

Usage:
    git diff --name-only BASE...HEAD | python scripts/classify_change_scope.py
    python scripts/classify_change_scope.py path/a path/b

Outputs GitHub Actions style ``key=value`` lines on stdout:
    scope=<docs-only|process-only|release-governance|runtime|unknown|mixed>
    runtime_changed=<true|false>
    backend_changed=<true|false>
    frontend_changed=<true|false>
    build_images=<true|false>
"""

from __future__ import annotations

import sys
from fnmatch import fnmatch


# Non-runtime paths never build production images.
PROCESS_GLOBS = (
    "AGENTS.md",
    "CLAUDE.md",
    "SKILL.md",
    "**/AGENTS.md",
    "**/CLAUDE.md",
    "**/SKILL.md",
    ".claude/**",
    ".cursor/**",
    ".trae/**",
    ".github/pull_request_template.md",
    ".github/labeler.yml",
    ".github/ISSUE_TEMPLATE/**",
    "scripts/ai_process_lint.py",
    "scripts/verify_image_build_source.py",
    "scripts/classify_change_scope.py",
    "scripts/*audit*.py",
)

DOCS_GLOBS = (
    "README",
    "README.*",
    "*.md",
    "**/*.md",
    "docs/**",
    "lmzj-docs/**",
)

# Release-governance paths require strict review but do not, on their own,
# build application images.
GOVERNANCE_GLOBS = (
    ".github/workflows/lmzj-pr-check.yml",
    ".github/workflows/lmzj-build-images.yml",
    ".github/workflows/lmzj-deploy-production.yml",
    "scripts/deploy-images.sh",
)

BACKEND_GLOBS = (
    "src/api/**",
    "src/api/Dockerfile",
)

FRONTEND_GLOBS = (
    "src/cook-web/**",
    "src/cook-web/Dockerfile",
)

# Runtime paths that are not service-specific build all images conservatively.
RUNTIME_GLOBS = (
    "src/**",
    "app/**",
    "Dockerfile",
    "**/Dockerfile",
    "docker/**",
    "docker-compose.yml",
    "docker-compose.*.yml",
    "**/package-lock.json",
    "**/pnpm-lock.yaml",
    "**/yarn.lock",
    "**/requirements*.txt",
    "**/pyproject.toml",
    "**/poetry.lock",
)


def _matches(path: str, globs: tuple[str, ...]) -> bool:
    return any(fnmatch(path, pattern) for pattern in globs)


def classify_path(path: str) -> str:
    """Return the scope of a single path. Order matters: most specific first."""
    if _matches(path, GOVERNANCE_GLOBS):
        return "release-governance"
    if _matches(path, PROCESS_GLOBS):
        return "process-only"
    if _matches(path, DOCS_GLOBS):
        return "docs-only"
    if _matches(path, RUNTIME_GLOBS):
        return "runtime"
    return "unknown"


def classify(paths: list[str]) -> dict[str, str]:
    scopes: set[str] = set()
    backend = False
    frontend = False
    runtime = False

    for raw in paths:
        path = raw.strip()
        if not path:
            continue
        scope = classify_path(path)
        scopes.add(scope)
        if scope in {"runtime", "unknown"}:
            runtime = True
            if _matches(path, BACKEND_GLOBS):
                backend = True
            elif _matches(path, FRONTEND_GLOBS):
                frontend = True
            else:
                # Shared runtime or unknown path: build both conservatively.
                backend = True
                frontend = True

    if not scopes:
        overall = "docs-only"
    elif len(scopes) == 1:
        overall = next(iter(scopes))
    else:
        overall = "mixed"

    build_images = runtime
    return {
        "scope": overall,
        "runtime_changed": str(runtime).lower(),
        "backend_changed": str(backend and runtime).lower(),
        "frontend_changed": str(frontend and runtime).lower(),
        "build_images": str(build_images).lower(),
    }


def main(argv: list[str]) -> int:
    if argv:
        paths = argv
    else:
        paths = sys.stdin.read().splitlines()
    result = classify(paths)
    for key, value in result.items():
        print(f"{key}={value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
