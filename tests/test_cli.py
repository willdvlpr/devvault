"""Integration tests for devvault.cli module."""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from click.testing import CliRunner

from devvault.cli import cli, parse_tags, read_content
from devvault import db, models


@pytest.fixture
def cli_runner():
    """Create a Click CLI test runner."""
    return CliRunner()


@pytest.fixture
def isolated_vault(cli_runner):
    """Create an isolated filesystem with initialized vault."""
    with cli_runner.isolated_filesystem():
        db.init_vault()
        yield Path.cwd()


class TestParseTags:
    """Tests for parse_tags function."""

    def test_parses_comma_separated(self):
        """parse_tags should parse comma-separated tags."""
        result = parse_tags("tag1,tag2,tag3")
        assert result == ["tag1", "tag2", "tag3"]

    def test_handles_whitespace(self):
        """parse_tags should handle whitespace around tags."""
        result = parse_tags("tag1 , tag2 , tag3")
        assert result == ["tag1", "tag2", "tag3"]

    def test_handles_empty_string(self):
        """parse_tags should return empty list for empty string."""
        result = parse_tags("")
        assert result == []

    def test_handles_none(self):
        """parse_tags should return empty list for None."""
        result = parse_tags(None)
        assert result == []

    def test_filters_empty_tags(self):
        """parse_tags should filter out empty tags."""
        result = parse_tags("tag1,,tag2,")
        assert result == ["tag1", "tag2"]


class TestReadContent:
    """Tests for read_content function."""

    def test_returns_string_directly(self):
        """read_content should return non-@ strings directly."""
        result = read_content("echo hello")
        assert result == "echo hello"

    def test_reads_from_file(self, isolated_vault):
        """read_content should read from file when prefixed with @."""
        # Create a test file
        test_file = Path("test_script.sh")
        test_file.write_text("#!/bin/bash\necho hello")

        result = read_content("@test_script.sh")
        assert result == "#!/bin/bash\necho hello"

    def test_exits_on_file_not_found(self, isolated_vault):
        """read_content should exit when file not found."""
        with pytest.raises(SystemExit):
            read_content("@nonexistent.sh")


class TestInitCommand:
    """Tests for the init command."""

    def test_creates_vault(self, cli_runner):
        """init should create a new vault."""
        with cli_runner.isolated_filesystem():
            result = cli_runner.invoke(cli, ["init"])
            assert result.exit_code == 0
            assert "initialized" in result.output.lower()
            assert db.vault_exists()

    def test_warns_if_vault_exists(self, isolated_vault, cli_runner):
        """init should warn if vault already exists."""
        result = cli_runner.invoke(cli, ["init"])
        assert "already exists" in result.output.lower()


class TestAddCommands:
    """Tests for the add subcommands."""

    def test_add_command(self, isolated_vault, cli_runner):
        """add command should add a command entry."""
        result = cli_runner.invoke(cli, [
            "add", "command",
            "-n", "test-cmd",
            "-d", "Test command",
            "-c", "echo hello",
            "-t", "test,shell",
        ])

        assert result.exit_code == 0
        assert "Added command" in result.output

        entry = db.get_entry("test-cmd")
        assert entry is not None
        assert entry["type"] == "command"
        assert entry["content"] == "echo hello"
        assert entry["tags"] == ["test", "shell"]

    def test_add_api(self, isolated_vault, cli_runner):
        """add api should add an API entry."""
        result = cli_runner.invoke(cli, [
            "add", "api",
            "-n", "test-api",
            "-d", "Test API",
            "--method", "POST",
            "--url", "https://api.example.com/test",
            "-H", "Content-Type:application/json",
            "-H", "Authorization:Bearer token",
            "-c", '{"key": "value"}',
            "-t", "api,test",
        ])

        assert result.exit_code == 0
        assert "Added API" in result.output

        entry = db.get_entry("test-api")
        assert entry is not None
        assert entry["type"] == "api"
        assert entry["metadata"]["method"] == "POST"
        assert entry["metadata"]["url"] == "https://api.example.com/test"
        assert entry["metadata"]["headers"]["Content-Type"] == "application/json"
        assert entry["metadata"]["headers"]["Authorization"] == "Bearer token"

    def test_add_snippet(self, isolated_vault, cli_runner):
        """add snippet should add a snippet entry."""
        result = cli_runner.invoke(cli, [
            "add", "snippet",
            "-n", "test-snippet",
            "-d", "Test snippet",
            "-c", "def hello(): pass",
            "-l", "python",
            "-t", "python,test",
        ])

        assert result.exit_code == 0
        assert "Added snippet" in result.output

        entry = db.get_entry("test-snippet")
        assert entry is not None
        assert entry["type"] == "snippet"
        assert entry["metadata"]["language"] == "python"

    def test_add_note(self, isolated_vault, cli_runner):
        """add note should add a note entry."""
        result = cli_runner.invoke(cli, [
            "add", "note",
            "-n", "test-note",
            "-d", "Test note",
            "-c", "This is a test note",
            "-t", "notes",
        ])

        assert result.exit_code == 0
        assert "Added note" in result.output

        entry = db.get_entry("test-note")
        assert entry is not None
        assert entry["type"] == "note"

    def test_add_file(self, isolated_vault, cli_runner):
        """add file should add a file entry."""
        result = cli_runner.invoke(cli, [
            "add", "file",
            "-n", "test-file",
            "-d", "Test file",
            "-c", "config: value",
            "-f", "config.yml",
            "-t", "config",
        ])

        assert result.exit_code == 0
        assert "Added file" in result.output

        entry = db.get_entry("test-file")
        assert entry is not None
        assert entry["type"] == "file"
        assert entry["metadata"]["filename"] == "config.yml"

    def test_add_playbook(self, isolated_vault, cli_runner):
        """add playbook should add a playbook entry."""
        result = cli_runner.invoke(cli, [
            "add", "playbook",
            "-n", "test-playbook",
            "-d", "Test playbook",
            "-c", "step1\nstep2",
            "-t", "deployment",
        ])

        assert result.exit_code == 0
        assert "Added playbook" in result.output

        entry = db.get_entry("test-playbook")
        assert entry is not None
        assert entry["type"] == "playbook"

    def test_add_command_from_file(self, isolated_vault, cli_runner):
        """add command should read content from file."""
        # Create a test file
        test_file = Path("script.sh")
        test_file.write_text("#!/bin/bash\necho hello")

        result = cli_runner.invoke(cli, [
            "add", "command",
            "-n", "from-file",
            "-d", "From file",
            "-c", "@script.sh",
        ])

        assert result.exit_code == 0
        entry = db.get_entry("from-file")
        assert "#!/bin/bash" in entry["content"]


class TestListCommand:
    """Tests for the list command."""

    def test_list_empty_vault(self, isolated_vault, cli_runner):
        """list should handle empty vault."""
        result = cli_runner.invoke(cli, ["list"])
        assert result.exit_code == 0
        assert "No entries found" in result.output

    def test_list_all_entries(self, isolated_vault, cli_runner):
        """list should show all entries."""
        # Add some entries
        cli_runner.invoke(cli, [
            "add", "command", "-n", "cmd1", "-d", "Command 1", "-c", "echo 1",
        ])
        cli_runner.invoke(cli, [
            "add", "note", "-n", "note1", "-d", "Note 1", "-c", "Note content",
        ])

        result = cli_runner.invoke(cli, ["list"])
        assert result.exit_code == 0
        assert "cmd1" in result.output
        assert "note1" in result.output

    def test_list_by_type(self, isolated_vault, cli_runner):
        """list --type should filter by type."""
        cli_runner.invoke(cli, [
            "add", "command", "-n", "cmd1", "-d", "Command 1", "-c", "echo 1",
        ])
        cli_runner.invoke(cli, [
            "add", "note", "-n", "note1", "-d", "Note 1", "-c", "Note content",
        ])

        result = cli_runner.invoke(cli, ["list", "--type", "command"])
        assert result.exit_code == 0
        assert "cmd1" in result.output
        assert "note1" not in result.output

    def test_list_by_tag(self, isolated_vault, cli_runner):
        """list -t should filter by tag."""
        cli_runner.invoke(cli, [
            "add", "command", "-n", "cmd1", "-d", "Command 1", "-c", "echo 1", "-t", "shell",
        ])
        cli_runner.invoke(cli, [
            "add", "command", "-n", "cmd2", "-d", "Command 2", "-c", "echo 2", "-t", "python",
        ])

        result = cli_runner.invoke(cli, ["list", "-t", "shell"])
        assert result.exit_code == 0
        assert "cmd1" in result.output
        assert "cmd2" not in result.output


class TestSearchCommand:
    """Tests for the search command."""

    def test_search_finds_matches(self, isolated_vault, cli_runner):
        """search should find matching entries."""
        cli_runner.invoke(cli, [
            "add", "command", "-n", "docker-build", "-d", "Build Docker image", "-c", "docker build .",
        ])
        cli_runner.invoke(cli, [
            "add", "command", "-n", "git-push", "-d", "Push to remote", "-c", "git push",
        ])

        result = cli_runner.invoke(cli, ["search", "docker"])
        assert result.exit_code == 0
        assert "docker-build" in result.output
        assert "git-push" not in result.output

    def test_search_no_matches(self, isolated_vault, cli_runner):
        """search should handle no matches."""
        cli_runner.invoke(cli, [
            "add", "command", "-n", "cmd1", "-d", "Command 1", "-c", "echo 1",
        ])

        result = cli_runner.invoke(cli, ["search", "nonexistent"])
        assert result.exit_code == 0
        assert "No entries found" in result.output


class TestShowCommand:
    """Tests for the show command."""

    def test_show_by_name(self, isolated_vault, cli_runner):
        """show should display entry by name."""
        cli_runner.invoke(cli, [
            "add", "command", "-n", "test-cmd", "-d", "Test command", "-c", "echo hello",
        ])

        result = cli_runner.invoke(cli, ["show", "test-cmd"])
        assert result.exit_code == 0
        assert "test-cmd" in result.output
        assert "echo hello" in result.output

    def test_show_by_id(self, isolated_vault, cli_runner):
        """show should display entry by ID."""
        cli_runner.invoke(cli, [
            "add", "command", "-n", "test-cmd", "-d", "Test command", "-c", "echo hello",
        ])

        entry = db.get_entry("test-cmd")
        result = cli_runner.invoke(cli, ["show", entry["id"]])
        assert result.exit_code == 0
        assert "test-cmd" in result.output

    def test_show_not_found(self, isolated_vault, cli_runner):
        """show should handle entry not found."""
        result = cli_runner.invoke(cli, ["show", "nonexistent"])
        assert "not found" in result.output.lower()


class TestRunCommand:
    """Tests for the run command."""

    def test_run_command_entry(self, isolated_vault, cli_runner):
        """run should execute command entry."""
        cli_runner.invoke(cli, [
            "add", "command", "-n", "test-cmd", "-d", "Test", "-c", "echo hello",
        ])

        result = cli_runner.invoke(cli, ["run", "test-cmd", "--yes"])
        assert result.exit_code == 0
        assert "hello" in result.output

    def test_run_not_found(self, isolated_vault, cli_runner):
        """run should handle entry not found."""
        result = cli_runner.invoke(cli, ["run", "nonexistent"])
        assert "not found" in result.output.lower()


class TestDeleteCommand:
    """Tests for the delete command."""

    def test_delete_with_confirmation(self, isolated_vault, cli_runner):
        """delete should remove entry with confirmation."""
        cli_runner.invoke(cli, [
            "add", "command", "-n", "test-cmd", "-d", "Test", "-c", "echo hello",
        ])

        result = cli_runner.invoke(cli, ["delete", "test-cmd", "--yes"])
        assert result.exit_code == 0
        assert "Deleted" in result.output
        assert db.get_entry("test-cmd") is None

    def test_delete_cancelled(self, isolated_vault, cli_runner):
        """delete should cancel when user says no."""
        cli_runner.invoke(cli, [
            "add", "command", "-n", "test-cmd", "-d", "Test", "-c", "echo hello",
        ])

        result = cli_runner.invoke(cli, ["delete", "test-cmd"], input="n\n")
        assert "Cancelled" in result.output
        assert db.get_entry("test-cmd") is not None

    def test_delete_not_found(self, isolated_vault, cli_runner):
        """delete should handle entry not found."""
        result = cli_runner.invoke(cli, ["delete", "nonexistent"])
        assert "not found" in result.output.lower()


class TestTagsCommand:
    """Tests for the tags command."""

    def test_tags_empty_vault(self, isolated_vault, cli_runner):
        """tags should handle empty vault."""
        result = cli_runner.invoke(cli, ["tags"])
        assert result.exit_code == 0
        assert "No tags found" in result.output

    def test_tags_lists_all(self, isolated_vault, cli_runner):
        """tags should list all unique tags."""
        cli_runner.invoke(cli, [
            "add", "command", "-n", "cmd1", "-d", "Command 1", "-c", "echo 1", "-t", "shell,linux",
        ])
        cli_runner.invoke(cli, [
            "add", "command", "-n", "cmd2", "-d", "Command 2", "-c", "echo 2", "-t", "shell,macos",
        ])

        result = cli_runner.invoke(cli, ["tags"])
        assert result.exit_code == 0
        assert "shell" in result.output
        assert "linux" in result.output
        assert "macos" in result.output


class TestExportCommand:
    """Tests for the export command."""

    def test_export_entry(self, isolated_vault, cli_runner):
        """export should write entry to JSON file."""
        cli_runner.invoke(cli, [
            "add", "command", "-n", "test-cmd", "-d", "Test", "-c", "echo hello", "-t", "test",
        ])

        result = cli_runner.invoke(cli, ["export", "test-cmd", "-o", "export.json"])
        assert result.exit_code == 0
        assert "Exported" in result.output

        with open("export.json") as f:
            exported = json.load(f)
        assert exported["name"] == "test-cmd"
        assert exported["content"] == "echo hello"

    def test_export_not_found(self, isolated_vault, cli_runner):
        """export should handle entry not found."""
        result = cli_runner.invoke(cli, ["export", "nonexistent", "-o", "export.json"])
        assert "not found" in result.output.lower()


class TestImportCommand:
    """Tests for the import command."""

    def test_import_entry(self, isolated_vault, cli_runner):
        """import should add entry from JSON file."""
        entry_data = {
            "type": "command",
            "name": "imported-cmd",
            "description": "Imported command",
            "content": "echo imported",
            "tags": ["imported"],
        }

        with open("import.json", "w") as f:
            json.dump(entry_data, f)

        result = cli_runner.invoke(cli, ["import", "import.json"])
        assert result.exit_code == 0
        assert "Imported" in result.output

        entry = db.get_entry("imported-cmd")
        assert entry is not None
        assert entry["content"] == "echo imported"

    def test_import_invalid_json(self, isolated_vault, cli_runner):
        """import should handle invalid JSON."""
        with open("invalid.json", "w") as f:
            f.write("not valid json")

        result = cli_runner.invoke(cli, ["import", "invalid.json"])
        assert "Invalid JSON" in result.output

    def test_import_missing_fields(self, isolated_vault, cli_runner):
        """import should validate required fields."""
        entry_data = {
            "type": "command",
            "name": "test",
            # Missing description and content
        }

        with open("incomplete.json", "w") as f:
            json.dump(entry_data, f)

        result = cli_runner.invoke(cli, ["import", "incomplete.json"])
        assert "Missing required field" in result.output

    def test_import_file_not_found(self, isolated_vault, cli_runner):
        """import should handle file not found."""
        result = cli_runner.invoke(cli, ["import", "nonexistent.json"])
        assert "not found" in result.output.lower()


class TestEditCommand:
    """Tests for the edit command."""

    def test_edit_not_found(self, isolated_vault, cli_runner):
        """edit should handle entry not found."""
        result = cli_runner.invoke(cli, ["edit", "nonexistent"])
        assert "not found" in result.output.lower()


class TestNoVaultErrors:
    """Tests for commands when vault doesn't exist."""

    def test_list_no_vault(self, cli_runner):
        """list should error when no vault exists."""
        with cli_runner.isolated_filesystem():
            result = cli_runner.invoke(cli, ["list"])
            assert "No vault found" in result.output

    def test_search_no_vault(self, cli_runner):
        """search should error when no vault exists."""
        with cli_runner.isolated_filesystem():
            result = cli_runner.invoke(cli, ["search", "test"])
            assert "No vault found" in result.output

    def test_show_no_vault(self, cli_runner):
        """show should error when no vault exists."""
        with cli_runner.isolated_filesystem():
            result = cli_runner.invoke(cli, ["show", "test"])
            assert "No vault found" in result.output

    def test_tags_no_vault(self, cli_runner):
        """tags should error when no vault exists."""
        with cli_runner.isolated_filesystem():
            result = cli_runner.invoke(cli, ["tags"])
            assert "No vault found" in result.output
