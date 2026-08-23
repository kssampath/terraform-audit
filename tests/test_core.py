from terraform_audit.core import find_tf_files, scan_file_for_tags, scan_line_for_secrets
from pathlib import Path

def test_detects_password():
    # Arrange — a line that clearly contains a hardcoded secret
    line = 'password = "hunter2"'

    # Act — run the function
    findings = scan_line_for_secrets(line, 1)

    # Assert — we expect exactly one finding, and it should be HIGH severity
    assert len(findings) == 1
    assert findings[0].severity == "HIGH"


def test_clean_line_has_no_findings():
    # Arrange — a normal line with no secret
    line = 'resource "azurerm_key_vault" "kv" {'

    # Act
    findings = scan_line_for_secrets(line, 1)

    # Assert — nothing should be flagged
    assert findings == []
    
from pathlib import Path
from terraform_audit.core import scan_line_for_secrets, scan_file_for_tags


def test_scan_file_for_tags(tmp_path):
    required_tags = ["Environment", "Owner"]
    terraform_content = '''resource "azurerm_storage_account" "example" {
  name = "examplestorageaccount"
  tags = {
    Environment = "Production"
  }
}
'''
    tf_file = tmp_path / "sample.tf"
    tf_file.write_text(terraform_content)

    findings = scan_file_for_tags(tf_file, required_tags)

    assert len(findings) == 1
    assert "Owner" in findings[0].message
# def test_find_tf_files():
#     # Arrange — create a temporary directory with some .tf files

def test_find_tf_files(tmp_path):
    # Arrange — create two .tf files and one non-.tf file in the temp dir
    (tmp_path / "main.tf").write_text("resource {}")
    (tmp_path / "variables.tf").write_text("variable {}")
    (tmp_path / "README.md").write_text("not terraform")
    # Assert — found exactly the two .tf files, ignored the .md
    subdir = tmp_path / "modules"
    subdir.mkdir()                          # create the subfolder
    (subdir / "nested.tf").write_text("resource {}")
    # Act
    result = find_tf_files(tmp_path)
    assert len(result) == 3                 # now finds the nested one too




