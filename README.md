# terraform-audit

[![CI](https://github.com/kssampath/terraform-audit/actions/workflows/ci.yml/badge.svg)](https://github.com/kssampath/terraform-audit/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

A command-line tool that audits Terraform (`.tf`) files for two common governance problems:

- 🔑 **Hardcoded secrets** — passwords, API keys, access keys, and private keys assigned as literal strings.
- 🏷️ **Missing required tags** — resources that don't carry the tags your organisation mandates (e.g. `owner`, `cost_center`, `environment`).

It walks a directory of Terraform, inspects each resource block, and reports findings with a severity, the line number, and a description.

## Why

Infrastructure-as-code makes it easy to accidentally commit a secret or ship a resource without governance tags. This tool provides a fast, dependency-light check that runs locally or in CI, catching those issues before they reach `main` or a live environment.

## Installation

Requires Python 3.10+.

```bash
git clone https://github.com/<your-username>/terraform-audit.git
cd terraform-audit
python -m pip install -e .
```

This installs the `tf-audit` command. (Using `python -m pip` rather than bare `pip` ensures the tool installs under the same interpreter you run.)

## Usage

Scan a directory of Terraform files:

```bash
tf-audit scan ./path/to/terraform
```

Specify which tags are required (comma-separated; defaults to `owner,cost_center,environment`):

```bash
tf-audit scan ./infra --required-tags owner,environment,team
```

See help:

```bash
tf-audit --help
tf-audit scan --help
```

If the `tf-audit` command isn't found (a PATH quirk on some Windows/Git Bash setups), you can always run it as a module:

```bash
python -m terraform_audit.cli scan ./path/to/terraform
```

## Example output

```
HIGH - Line 12: Possible hardcoded password
LOW - Line 10: Resource azurerm_key_vault.key_vault missing required tag: 'owner'
LOW - Line 10: Resource azurerm_key_vault.key_vault missing required tag: 'cost_center'
```

## How it works

- **File discovery** — recursively finds every `.tf` file under the given path.
- **Secret detection** — scans each line with regular expressions for sensitive assignments (e.g. `password = "..."`). Covers passwords, secrets, API keys, access keys, private keys, tokens, and connection strings. Reports the *type* of secret, never the value.
- **Tag checking** — parses each `resource "..." "..." { ... }` block by tracking brace depth, then checks whether each required tag appears within the block.

Findings from both checks are collected into a single list of `Finding` objects (severity, line, message) and printed as one report.

## Development

Run the tests:

```bash
python -m pip install -e ".[dev]"
python -m pytest
```

Tests are self-contained (they generate their own sample Terraform via pytest's `tmp_path` fixture), so they run identically on any machine and in CI.

## Continuous integration

A GitHub Actions workflow (`.github/workflows/ci.yml`) runs the test suite on every push, on a clean machine, so regressions and hidden local dependencies are caught automatically.

## Limitations & design notes

This tool favours simplicity and zero heavy dependencies over exhaustive correctness. Known, deliberate simplifications:

- **Regex/line-based parsing, not a full HCL parser.** Resource blocks are identified by tracking `{`/`}` depth per line. This is reliable for `terraform fmt`-formatted files but could miscount if braces appear inside string values or comments. A production-grade version would parse HCL properly using [`python-hcl2`](https://pypi.org/project/python-hcl2/).
- **Tag matching is case-sensitive.** `Environment` and `environment` are treated as different tags. This matches Azure's case-sensitive tag semantics, but is worth being aware of.
- **Tag presence, not tag scope.** A required tag is considered present if it appears as an assignment anywhere within the resource block; the tool does not strictly verify it sits inside a `tags = { }` block.
- **Resource types that can't be tagged** (e.g. `azurerm_role_assignment`) are still checked and will report missing tags. Filtering these out is a candidate for a future version.

## Possible future work

- Use `python-hcl2` for robust parsing.
- Skip resource types that don't support tags.
- Configurable severity thresholds and a `--fail-on` flag to control the exit code for CI gating.
- JSON output format for machine consumption.

