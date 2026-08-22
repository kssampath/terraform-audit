# tf-audit

A lightweight, dependency-light CLI that scans Terraform code for common
security and hygiene problems: hardcoded secrets, resources exposed to the
public network, and missing or incomplete tags. Designed to run locally and
as a **fail-the-build gate in CI**.

Built as a companion to a modernised Azure Terraform platform — it catches the
same class of misconfiguration that the migration hardened by hand (for
example, storage accounts left with `default_action = "Allow"`).

## Install

```bash
pip install -e .
```

This installs a `tf-audit` console command.

## Usage

```bash
# Scan a directory (table output)
tf-audit scan ./infra

# Machine-readable output
tf-audit scan ./infra --format json

# Fail the process if any HIGH-severity issue is found (for CI)
tf-audit scan ./infra --fail-on high
```

Example output:

```
Found 7 issue(s):
  HIGH    TF001  infra/main.tf:12
           Possible hardcoded secret assigned to a string literal
  HIGH    TF002  infra/main.tf:31
           Resource has public network access enabled
  MEDIUM  TF003  infra/main.tf:34
           Network rule default_action is 'Allow' (expected 'Deny')
  ...
Summary: 2 high, 1 medium, 4 low
```

## Rules

| ID    | Severity | What it catches |
|-------|----------|-----------------|
| TF001 | HIGH     | A secret-like key assigned a string literal (ignores `var.`/`data.` references and comments) |
| TF002 | HIGH     | `public_network_access_enabled = true` |
| TF003 | MEDIUM   | Network `default_action = "Allow"` (expected `Deny`) |
| TF004 | LOW      | A taggable resource with no `tags` block |
| TF005 | LOW      | A `tags` block missing a required tag (`environment`, `owner`) |

Resource types that don't take tags (subnets, role assignments, etc.) are
excluded from TF004/TF005.

## Exit codes

| Code | Meaning |
|------|---------|
| 0    | No findings at or above the `--fail-on` threshold |
| 1    | Findings at or above the threshold (build should fail) |
| 2    | Usage or runtime error |

`--fail-on` accepts `low`, `medium`, `high`, or `never` (default). With
`never`, the tool always exits 0 and is purely informational.

## Use in CI

Because it exits non-zero on findings, it drops into any pipeline as a gate
alongside `tfsec`/`checkov`:

```yaml
- name: Custom Terraform policy audit
  run: |
    pip install -e .
    tf-audit scan ./infra --fail-on high
```

## Development

```bash
pip install -e ".[dev]"
pytest          # run the test suite
ruff check .    # lint
black .         # format
```

## Design notes

This is a **heuristic linter, not an HCL parser**. Rules operate on file text
with regex and light brace-tracking, which keeps the tool fast and free of a
Terraform/HCL parsing dependency. The trade-off is that it doesn't understand
Terraform semantics — it can't resolve variables or evaluate expressions — so
it favours obvious, high-signal patterns over exhaustive coverage. For deep
policy-as-code, pair it with `checkov` or OPA/Conftest; this tool exists to
encode a few project-specific rules those don't cover, and to demonstrate a
clean, tested, CI-ready Python CLI.
