from pathlib import Path
import re
from dataclasses import dataclass


@dataclass
class Finding:
    severity: str
    line: int
    message: str

def find_tf_files(path: Path):
    """
    Recursively find all Terraform files in the given path.

    Args:
        path (Path): The path to search for Terraform files.

    Returns:
        List[Path]: A list of paths to Terraform files.
    """
    return list(Path(path).rglob("*.tf"))
def scan_line_for_secrets(line: str, lineno: int) -> list[Finding]:
    """
    Scan a line of text for potential secrets.

    Args:
        line (str): The line of text to scan.
        lineno (int): The line number.

    Returns:
        List[Finding]: A list of potential secrets found on the line.
    """
    patterns = [
    # HIGH severity
    ("password",          "HIGH",   r'(?i)password\s*=\s*["\'].*?["\']'),
    ("secret",            "HIGH",   r'(?i)secret\s*=\s*["\'].*?["\']'),
    ("private key",       "HIGH",   r'(?i)private_key\s*=\s*["\'].*?["\']'),
    ("connection string", "HIGH",   r'(?i)connection_string\s*=\s*["\'].*?["\']'),
    # MEDIUM severity
    ("API key",           "MEDIUM", r'(?i)api_key\s*=\s*["\'].*?["\']'),
    ("access key",        "MEDIUM", r'(?i)access_key\s*=\s*["\'].*?["\']'),
    ("token",             "MEDIUM", r'(?i)token\s*=\s*["\'].*?["\']'),
    # LOW severity
    ("username",          "LOW",    r'(?i)username\s*=\s*["\'].*?["\']'),
    ("email",             "LOW",    r'(?i)email\s*=\s*["\'].*?["\']'),
    ]

    findings = []
    for label, severity, pattern in patterns:
        if re.search(pattern, line):
            findings.append(Finding(
                severity=severity,
                line=lineno,
                message=f"Possible hardcoded {label}"
            ))
    return findings

def scan_file_for_tags(filepath: Path, required_tags: list[str]) -> list[Finding]:
    """
    Scan a Terraform file for required tags.

    Args:
        filepath (Path): The path to the Terraform file.
        required_tags (list[str]): A list of required tags to check for.

    Returns:
        List[Finding]: A list of findings related to missing tags.
    """
    findings = []
    with open(filepath, 'r') as file:
        content = file.read()
        for tag in required_tags:
            if f'tags = {{' in content and tag not in content:
                findings.append(Finding(
                    severity="MEDIUM",
                    line=0,
                    message=f"Missing required tag: {tag} in file {filepath.name}"
                ))
    return findings

def scan_file_for_tags(filepath: Path, required_tags: list[str]) -> list[Finding]:
    """
    Scan a Terraform file for required tags.

    Args:
        filepath (Path): The path to the Terraform file.
        required_tags (list[str]): A list of required tags to check for.

    Returns:
        List[Finding]: A list of findings related to missing tags.
    """
    lines = filepath.read_text().splitlines()
    depth = 0
    inside_resource = False
    resource_start_line = 0
    resource_label = ""
    resource_text = []          # collect the block's lines
    findings = []
    for lineno, line in enumerate(lines, start=1):
        m = re.match(r'\s*resource\s+"([^"]+)"\s+"([^"]+)"', line)
        if m:
            inside_resource = True
            resource_label = f"{m.group(1)}.{m.group(2)}"
            resource_start_line = lineno
            resource_text = []

        if inside_resource:
            resource_text.append(line)
            depth += line.count("{")
            depth -= line.count("}")

            if depth == 0 and "}" in line:
                block = "\n".join(resource_text)          # the whole resource block as one string
                for tag in required_tags:
                    # look for the tag as a key: e.g.  owner = "..."
                    if not re.search(rf'{tag}\s*=', block):
                        findings.append(Finding(
                            severity="LOW",
                            line=resource_start_line,
                            message=f"Resource {resource_label} missing required tag: '{tag}'"
                        ))
                inside_resource = False
    return findings