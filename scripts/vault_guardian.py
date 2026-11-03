#!/usr/bin/env python3
"""Fail-closed admission checks for Business Code Vault modules.

This validates the presence and shape of required evidence. It does not claim
that a human/security review is infallible or independently reproduce every
language-specific test suite.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
MODULES = ROOT / "modules"
SHA40 = re.compile(r"^[0-9a-f]{40}$", re.IGNORECASE)
TEST_FILE_PATTERNS = ("test_*.py", "*_test.py", "*.test.*", "*.spec.*")


def nonempty(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def https_url(value: object) -> bool:
    if not nonempty(value):
        return False
    parsed = urlparse(value.strip())
    return parsed.scheme == "https" and bool(parsed.netloc)


def test_files(folder: Path) -> list[Path]:
    found: set[Path] = set()
    for pattern in TEST_FILE_PATTERNS:
        found.update(p for p in folder.rglob(pattern) if p.is_file())
    return sorted(found)


def validate(module_dir: Path) -> list[str]:
    errors: list[str] = []
    manifest = module_dir / "module.json"
    if not manifest.is_file():
        return [f"{module_dir.relative_to(ROOT)}: missing module.json"]

    try:
        data = json.loads(manifest.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"{manifest.relative_to(ROOT)}: invalid JSON ({exc})"]

    def need(condition: bool, message: str) -> None:
        if not condition:
            errors.append(message)

    for key in ("id", "name", "version", "language", "runtime"):
        need(nonempty(data.get(key)), f"missing/empty '{key}'")

    need(data.get("status") == "verified",
         "status must be exactly 'verified' (candidate/imported/deprecated are not admissible)")

    source = data.get("source")
    need(isinstance(source, dict), "'source' must be an object")
    if isinstance(source, dict):
        for key in ("repository", "path", "ref"):
            need(nonempty(source.get(key)), f"source.{key} is required")
        need(bool(SHA40.fullmatch(str(source.get("commit", "")))),
             "source.commit must be a full 40-character Git commit SHA")

    need(isinstance(data.get("dependencies"), list),
         "'dependencies' must be a list (use [] when there are none)")
    need(nonempty(data.get("installation")), "'installation' instructions are required")
    need(nonempty(data.get("usage_example")), "'usage_example' is required")

    compatibility = data.get("compatibility")
    need(isinstance(compatibility, list) and len(compatibility) > 0,
         "'compatibility' must list at least one tested environment")

    tests = data.get("tests")
    need(isinstance(tests, dict), "'tests' must be an object")
    if isinstance(tests, dict):
        commands = tests.get("commands")
        need(isinstance(commands, list) and len(commands) > 0
             and all(nonempty(item) for item in commands),
             "tests.commands must contain the exact commands executed")
        need(tests.get("result") == "PASS",
             "tests.result must be exactly 'PASS'")
        need(https_url(tests.get("ci_run_url")),
             "tests.ci_run_url must link to a real HTTPS CI/test run")

    tests_dir = module_dir / "tests"
    need(tests_dir.is_dir(), "module must include a tests/ directory")
    if tests_dir.is_dir():
        need(bool(test_files(tests_dir)),
             "tests/ must contain at least one recognizable test file")

    security = data.get("security_review")
    need(isinstance(security, dict), "'security_review' must be an object")
    if isinstance(security, dict):
        need(security.get("result") == "PASS",
             "security_review.result must be exactly 'PASS'")
        need(nonempty(security.get("reviewer")),
             "security_review.reviewer is required")
        need(nonempty(security.get("date")),
             "security_review.date is required")
        need(https_url(security.get("evidence_url")),
             "security_review.evidence_url must link to HTTPS evidence")

    portability = data.get("portability")
    need(isinstance(portability, dict), "'portability' must be an object")
    if isinstance(portability, dict):
        need(portability.get("result") == "PASS",
             "portability.result must be exactly 'PASS'")
        need(https_url(portability.get("evidence_url")),
             "portability.evidence_url must link to HTTPS evidence")

    need(not data.get("known_blockers"),
         "'known_blockers' must be absent or an empty list")
    blockers = data.get("known_blockers")
    need(blockers is None or blockers == [],
         "known_blockers must be empty; unresolved blockers reject admission")

    return errors


def main() -> int:
    if not MODULES.exists():
        print("PASS: no modules are present; nothing to admit.")
        return 0

    module_dirs = sorted(p.parent for p in MODULES.rglob("module.json"))
    # A module folder without its required manifest must not silently pass.
    candidate_dirs = sorted(p for p in MODULES.iterdir() if p.is_dir())
    missing_manifests = [p for p in candidate_dirs if not (p / "module.json").is_file()]

    failures: list[str] = []
    for folder in missing_manifests:
        failures.append(f"{folder.relative_to(ROOT)}: missing module.json at module root")
    for folder in module_dirs:
        failures.extend(f"{folder.relative_to(ROOT)}: {item}" for item in validate(folder))

    if failures:
        print("REJECTED: Vault Guardian admission gate failed.")
        for failure in failures:
            print(f" - {failure}")
        return 1

    if not module_dirs:
        print("PASS: no modules are present; nothing to admit.")
    else:
        print(f"PASS: {len(module_dirs)} module(s) satisfy the declared admission checks.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
