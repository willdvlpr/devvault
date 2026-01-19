"""Unit tests for devvault.utils module."""

from unittest.mock import MagicMock, patch

import pytest
from rich.panel import Panel
from rich.table import Table

from devvault.utils import (
    confirm,
    extract_variables,
    format_entry_detail,
    format_entry_table,
    get_syntax_lexer,
    print_error,
    print_success,
    print_warning,
    prompt_for_variables,
    substitute_variables,
)


class TestExtractVariables:
    """Tests for extract_variables function."""

    def test_extracts_single_variable(self):
        """extract_variables should extract a single variable."""
        result = extract_variables("Hello {{NAME}}")
        assert result == ["NAME"]

    def test_extracts_multiple_variables(self):
        """extract_variables should extract multiple variables."""
        result = extract_variables("{{USER}}@{{HOST}}:{{PORT}}")
        assert result == ["USER", "HOST", "PORT"]

    def test_returns_empty_for_no_variables(self):
        """extract_variables should return empty list when no variables."""
        result = extract_variables("Hello World")
        assert result == []

    def test_extracts_duplicate_variables(self):
        """extract_variables should extract duplicate variables."""
        result = extract_variables("{{VAR}} and {{VAR}} again")
        assert result == ["VAR", "VAR"]

    def test_handles_alphanumeric_variables(self):
        """extract_variables should handle alphanumeric variable names."""
        result = extract_variables("{{VAR1}} {{var2}} {{VAR_3}}")
        assert result == ["VAR1", "var2", "VAR_3"]

    def test_ignores_malformed_placeholders(self):
        """extract_variables should ignore malformed placeholders."""
        result = extract_variables("{{ VAR }} {VAR} {{VAR}")
        assert result == []

    def test_handles_empty_string(self):
        """extract_variables should handle empty string."""
        result = extract_variables("")
        assert result == []


class TestSubstituteVariables:
    """Tests for substitute_variables function."""

    def test_substitutes_single_variable(self):
        """substitute_variables should substitute a single variable."""
        result = substitute_variables("Hello {{NAME}}", {"NAME": "World"})
        assert result == "Hello World"

    def test_substitutes_multiple_variables(self):
        """substitute_variables should substitute multiple variables."""
        result = substitute_variables(
            "{{USER}}@{{HOST}}",
            {"USER": "admin", "HOST": "server.com"},
        )
        assert result == "admin@server.com"

    def test_substitutes_duplicate_occurrences(self):
        """substitute_variables should substitute all occurrences."""
        result = substitute_variables(
            "{{VAR}} and {{VAR}}",
            {"VAR": "value"},
        )
        assert result == "value and value"

    def test_preserves_unmatched_placeholders(self):
        """substitute_variables should preserve unmatched placeholders."""
        result = substitute_variables(
            "{{KNOWN}} and {{UNKNOWN}}",
            {"KNOWN": "value"},
        )
        assert result == "value and {{UNKNOWN}}"

    def test_handles_empty_variables(self):
        """substitute_variables should handle empty variables dict."""
        result = substitute_variables("Hello {{NAME}}", {})
        assert result == "Hello {{NAME}}"

    def test_handles_no_placeholders(self):
        """substitute_variables should handle content with no placeholders."""
        result = substitute_variables("Hello World", {"NAME": "Test"})
        assert result == "Hello World"

    def test_handles_empty_value(self):
        """substitute_variables should handle empty string values."""
        result = substitute_variables("Hello {{NAME}}!", {"NAME": ""})
        assert result == "Hello !"


class TestPromptForVariables:
    """Tests for prompt_for_variables function."""

    def test_prompts_for_each_variable(self):
        """prompt_for_variables should prompt for each variable."""
        with patch("devvault.utils.console") as mock_console:
            mock_console.input.side_effect = ["value1", "value2"]
            result = prompt_for_variables(["VAR1", "VAR2"])

            assert result == {"VAR1": "value1", "VAR2": "value2"}
            assert mock_console.input.call_count == 2

    def test_returns_empty_for_no_variables(self):
        """prompt_for_variables should return empty dict for no variables."""
        with patch("devvault.utils.console") as mock_console:
            result = prompt_for_variables([])
            assert result == {}
            mock_console.input.assert_not_called()


class TestGetSyntaxLexer:
    """Tests for get_syntax_lexer function."""

    def test_returns_bash_for_command(self):
        """get_syntax_lexer should return 'bash' for command type."""
        result = get_syntax_lexer("command", "ls -la")
        assert result == "bash"

    def test_returns_json_for_api(self):
        """get_syntax_lexer should return 'json' for API type."""
        result = get_syntax_lexer("api", '{"key": "value"}')
        assert result == "json"

    def test_detects_python_snippet(self):
        """get_syntax_lexer should detect Python in snippets."""
        result = get_syntax_lexer("snippet", "def hello():\n    pass")
        assert result == "python"

        result = get_syntax_lexer("snippet", "class MyClass:\n    pass")
        assert result == "python"

        result = get_syntax_lexer("snippet", "import os\nprint(os)")
        assert result == "python"

        result = get_syntax_lexer("snippet", "from os import path")
        assert result == "python"

    def test_detects_javascript_snippet(self):
        """get_syntax_lexer should detect JavaScript in snippets."""
        result = get_syntax_lexer("snippet", "function hello() {}")
        assert result == "javascript"

        result = get_syntax_lexer("snippet", "const x = 1;")
        assert result == "javascript"

        result = get_syntax_lexer("snippet", "let y = 2;")
        assert result == "javascript"

        result = get_syntax_lexer("snippet", "var z = 3;")
        assert result == "javascript"

    def test_detects_html_snippet(self):
        """get_syntax_lexer should detect HTML in snippets."""
        result = get_syntax_lexer("snippet", "<div>Hello</div>")
        assert result == "html"

        result = get_syntax_lexer("snippet", "<!DOCTYPE html>")
        assert result == "html"

    def test_returns_none_for_unknown_snippet(self):
        """get_syntax_lexer should return None for unknown snippet type."""
        result = get_syntax_lexer("snippet", "some random text")
        assert result is None

    def test_returns_none_for_note(self):
        """get_syntax_lexer should return None for note type."""
        result = get_syntax_lexer("note", "some text")
        assert result is None

    def test_returns_none_for_file(self):
        """get_syntax_lexer should return None for file type."""
        result = get_syntax_lexer("file", "config data")
        assert result is None


class TestFormatEntryTable:
    """Tests for format_entry_table function."""

    def test_returns_table(self):
        """format_entry_table should return a rich Table."""
        entries = [
            {
                "id": "abc12345",
                "type": "command",
                "name": "test",
                "description": "Test description",
                "tags": ["tag1"],
            }
        ]
        result = format_entry_table(entries)
        assert isinstance(result, Table)

    def test_handles_empty_list(self):
        """format_entry_table should handle empty list."""
        result = format_entry_table([])
        assert isinstance(result, Table)

    def test_handles_missing_optional_fields(self):
        """format_entry_table should handle missing optional fields."""
        entries = [
            {
                "id": "abc12345",
                "type": "command",
                "name": "test",
            }
        ]
        result = format_entry_table(entries)
        assert isinstance(result, Table)

    def test_truncates_long_description(self):
        """format_entry_table should truncate long descriptions."""
        entries = [
            {
                "id": "abc12345",
                "type": "command",
                "name": "test",
                "description": "A" * 100,  # Very long description
                "tags": [],
            }
        ]
        result = format_entry_table(entries)
        assert isinstance(result, Table)


class TestFormatEntryDetail:
    """Tests for format_entry_detail function."""

    def test_returns_panel(self):
        """format_entry_detail should return a rich Panel."""
        entry = {
            "id": "abc12345",
            "type": "command",
            "name": "test",
            "description": "Test description",
            "content": "echo hello",
            "tags": ["tag1"],
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
        }
        result = format_entry_detail(entry)
        assert isinstance(result, Panel)

    def test_handles_api_entry_with_metadata(self):
        """format_entry_detail should handle API entry with metadata."""
        entry = {
            "id": "abc12345",
            "type": "api",
            "name": "test-api",
            "description": "Test API",
            "content": '{"key": "value"}',
            "tags": ["api"],
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
            "metadata": {
                "method": "POST",
                "url": "https://api.example.com/test",
                "headers": {"Content-Type": "application/json"},
            },
        }
        result = format_entry_detail(entry)
        assert isinstance(result, Panel)

    def test_handles_missing_optional_fields(self):
        """format_entry_detail should handle missing optional fields."""
        entry = {
            "id": "abc12345",
            "type": "command",
            "name": "test",
        }
        result = format_entry_detail(entry)
        assert isinstance(result, Panel)


class TestPrintFunctions:
    """Tests for print_success, print_error, print_warning functions."""

    def test_print_success(self):
        """print_success should print green message."""
        with patch("devvault.utils.console") as mock_console:
            print_success("Success message")
            mock_console.print.assert_called_once()
            call_args = mock_console.print.call_args[0][0]
            assert "Success message" in call_args
            assert "green" in call_args

    def test_print_error(self):
        """print_error should print red error message."""
        with patch("devvault.utils.console") as mock_console:
            print_error("Error message")
            mock_console.print.assert_called_once()
            call_args = mock_console.print.call_args[0][0]
            assert "Error message" in call_args
            assert "red" in call_args

    def test_print_warning(self):
        """print_warning should print yellow warning message."""
        with patch("devvault.utils.console") as mock_console:
            print_warning("Warning message")
            mock_console.print.assert_called_once()
            call_args = mock_console.print.call_args[0][0]
            assert "Warning message" in call_args
            assert "yellow" in call_args


class TestConfirm:
    """Tests for confirm function."""

    @pytest.mark.parametrize("response", ["y", "Y", "yes", "YES", "Yes"])
    def test_returns_true_for_yes(self, response):
        """confirm should return True for yes responses."""
        with patch("devvault.utils.console") as mock_console:
            mock_console.input.return_value = response
            result = confirm("Continue?")
            assert result is True

    @pytest.mark.parametrize("response", ["n", "N", "no", "NO", "", "x", "anything"])
    def test_returns_false_for_other(self, response):
        """confirm should return False for non-yes responses."""
        with patch("devvault.utils.console") as mock_console:
            mock_console.input.return_value = response
            result = confirm("Continue?")
            assert result is False

    def test_displays_message(self):
        """confirm should display the message."""
        with patch("devvault.utils.console") as mock_console:
            mock_console.input.return_value = "n"
            confirm("Are you sure?")
            call_args = mock_console.input.call_args[0][0]
            assert "Are you sure?" in call_args
