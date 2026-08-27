import click
from pathlib import Path
from terraform_audit.core import find_tf_files, scan_line_for_secrets, scan_file_for_tags


@click.group()                      # ← NEW: the top-level group "tf-audit"
def cli():
    """Audit Terraform files for secrets and missing tags."""
    pass                            # the group itself does nothing; it just holds subcommands


@cli.command()                      # ← CHANGED: was @click.command(); now "a command under cli"
@click.argument("path")
@click.option("--required-tags", default="owner,cost_center,environment",
              help="Comma-separated required tags")
def scan(path, required_tags):
    required_tags_list = [tag.strip() for tag in required_tags.split(",")]
    all_findings = []
    for tf_file in find_tf_files(Path(path)):
        all_findings.extend(scan_file_for_tags(tf_file, required_tags_list))
        for lineno, line in enumerate(tf_file.read_text().splitlines(), start=1):
            all_findings.extend(scan_line_for_secrets(line, lineno))
    for finding in all_findings:
        click.echo(f"{finding.severity} - Line {finding.line}: {finding.message}")


if __name__ == "__main__":
    cli()                           # ← run the GROUP, not scan directly