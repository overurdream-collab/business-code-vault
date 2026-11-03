# Vault Guardian — Mandatory Admission Policy

## Purpose

Vault Guardian is the fail-closed admission gate for this repository. Its job is
to prevent incomplete, untested, undocumented, or uncleared modules from being
accepted as reusable assets.

## Non-negotiable rule

**No evidence, no admission.** A module is rejected when any required field,
test artifact, test result, security evidence, portability evidence, or source
traceability item is missing or invalid. A developer's statement that a module
is "done" is not evidence.

## Required evidence for every module

Each module must live in its own directory under `modules/<module-id>/` and
contain:

- `module.json` following the admission schema below.
- A `tests/` directory with actual recognizable test files.
- A full 40-character source commit SHA and exact source repository/path/ref.
- Exact test commands, a PASS result, and a link to the corresponding CI/test run.
- A recorded security review with reviewer, date, PASS result, and evidence link.
- A portability result of PASS with evidence from installation/use outside the
  original source project.
- Dependencies, compatibility, installation instructions, and a usage example.
- No unresolved blockers.

## Admission manifest

The required JSON shape is:

```json
{
  "id": "BCL-UTIL-001",
  "name": "Example module",
  "version": "1.0.0",
  "status": "verified",
  "language": "Python",
  "runtime": "Python 3.12",
  "source": {
    "repository": "owner/source-repository",
    "path": "src/example",
    "ref": "main",
    "commit": "0123456789abcdef0123456789abcdef01234567"
  },
  "dependencies": [],
  "compatibility": ["Python 3.12 on Ubuntu 24.04"],
  "installation": "Exact reproducible installation steps",
  "usage_example": "A minimal working example",
  "tests": {
    "commands": ["python -m unittest discover -s tests"],
    "result": "PASS",
    "ci_run_url": "https://github.com/owner/repo/actions/runs/123"
  },
  "security_review": {
    "result": "PASS",
    "reviewer": "Reviewer identity",
    "date": "2026-11-03",
    "evidence_url": "https://github.com/owner/repo/security"
  },
  "portability": {
    "result": "PASS",
    "evidence_url": "https://github.com/owner/repo/actions/runs/456"
  },
  "known_blockers": []
}
```

The example values are illustrative only; they are not test evidence and must
never be copied as proof.

## What the gate does

On pull requests that change modules, GitHub Actions runs
`scripts/vault_guardian.py`. It rejects missing manifests, incomplete required
metadata, invalid source SHAs, absent test files, non-PASS results, missing
evidence links, unresolved blockers, and modules whose status is not exactly
`verified`.

## Important limits and required repository setting

The script checks evidence structure and the presence of test files; it does
not independently prove that a linked CI run is genuine, that every test is
adequate, or that a security review is infallible. Reviewers must open and
inspect the linked evidence before approval. Language-specific tests must be
run and recorded before a module is proposed.

To make the gate technically mandatory, repository administrators must enable
branch protection/rulesets for `main` and require the status check
**Vault Guardian / admission-gate** before merging. Also require pull requests
and at least one independent approval. Until those GitHub settings are enabled,
the workflow reports failures but a user with direct write/admin access may
still bypass it.

## Rejection policy

Rejected candidates stay in their source projects or private working branches.
They are not copied into the accepted vault as incomplete samples. Do not label
a module Verified or Reuse-tested without the relevant evidence. Reuse-tested
requires a successful installation and test in a separate target project.
