import click
from pathlib import Path
from terraform_audit.core import find_tf_files, scan_line_for_secrets, scan_file_for_tags
SEVERITY = {"LOW" : 1, "MEDIUM": 2, "HIGH": 3}

@click.group()                      # ← NEW: the top-level group "tf-audit"
def cli():
    """Audit Terraform files for secrets and missing tags."""
    pass                            # the group itself does nothing; it just holds subcommands


@cli.command()                      # ← CHANGED: was @click.command(); now "a command under cli"
@click.argument("path")
@click.option("--required-tags", default="owner,cost_center,environment", help="Comma-separated required tags")
@click.option("--fail-on", type=click.Choice(["LOW", "MEDIUM", "HIGH"], case_sensitive=False), default=None, help="Exit non-zero if any finding is at or above this severity")
def scan(path, required_tags, fail_on):
    required_tags_list = [tag.strip() for tag in required_tags.split(",")]
    all_findings = []
    for tf_file in find_tf_files(Path(path)):
        all_findings.extend(scan_file_for_tags(tf_file, required_tags_list))
        for lineno, line in enumerate(tf_file.read_text().splitlines(), start=1):
            all_findings.extend(scan_line_for_secrets(line, lineno))
    for finding in all_findings:
        click.echo(f"{finding.severity} - Line {finding.line}: {finding.message}")

    if fail_on:
        fail_severity = SEVERITY[fail_on.upper()]
        count = sum(1 for finding in all_findings if SEVERITY[finding.severity] >= fail_severity)
        if count > 0:
            raise click.ClickException(f"{count} finding(s) at or above {fail_on}")

if __name__ == "__main__":
    cli()                           # ← run the GROUP, not scan directly