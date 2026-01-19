"""Unit tests for devvault.executor module."""

import subprocess
from unittest.mock import MagicMock, patch, call

import pytest
import responses
from requests import Response

from devvault.executor import (
    execute_api,
    execute_command,
    execute_entry,
    execute_playbook,
)
from devvault import models


class TestExecuteCommand:
    """Tests for execute_command function."""

    def test_returns_tuple(self):
        """execute_command should return (returncode, stdout, stderr) tuple."""
        result = execute_command("echo hello")
        assert isinstance(result, tuple)
        assert len(result) == 3

    def test_captures_stdout(self):
        """execute_command should capture stdout."""
        returncode, stdout, stderr = execute_command("echo hello")
        assert "hello" in stdout

    def test_captures_stderr(self):
        """execute_command should capture stderr."""
        returncode, stdout, stderr = execute_command("echo error >&2")
        assert "error" in stderr

    def test_returns_zero_for_success(self):
        """execute_command should return 0 for successful commands."""
        returncode, stdout, stderr = execute_command("true")
        assert returncode == 0

    def test_returns_nonzero_for_failure(self):
        """execute_command should return non-zero for failed commands."""
        returncode, stdout, stderr = execute_command("false")
        assert returncode != 0

    def test_handles_complex_commands(self):
        """execute_command should handle complex shell commands."""
        returncode, stdout, stderr = execute_command("echo 'line1'; echo 'line2'")
        assert "line1" in stdout
        assert "line2" in stdout

    def test_handles_piped_commands(self):
        """execute_command should handle piped commands."""
        returncode, stdout, stderr = execute_command("echo 'hello world' | tr 'h' 'H'")
        assert "Hello" in stdout


class TestExecuteApi:
    """Tests for execute_api function."""

    @responses.activate
    def test_makes_get_request(self):
        """execute_api should make GET requests."""
        responses.add(
            responses.GET,
            "https://api.example.com/test",
            json={"success": True},
            status=200,
        )

        entry = models.create_entry(
            entry_type="api",
            name="test-api",
            description="Test API",
            content="",
            metadata={
                "method": "GET",
                "url": "https://api.example.com/test",
                "headers": {},
            },
        )

        response = execute_api(entry)
        assert response is not None
        assert response.status_code == 200

    @responses.activate
    def test_makes_post_request_with_json_body(self):
        """execute_api should make POST requests with JSON body."""
        responses.add(
            responses.POST,
            "https://api.example.com/test",
            json={"id": 1},
            status=201,
        )

        entry = models.create_entry(
            entry_type="api",
            name="test-api",
            description="Test API",
            content='{"name": "test"}',
            metadata={
                "method": "POST",
                "url": "https://api.example.com/test",
                "headers": {"Content-Type": "application/json"},
            },
        )

        response = execute_api(entry)
        assert response is not None
        assert response.status_code == 201

    @responses.activate
    def test_makes_put_request(self):
        """execute_api should make PUT requests."""
        responses.add(
            responses.PUT,
            "https://api.example.com/test/1",
            json={"updated": True},
            status=200,
        )

        entry = models.create_entry(
            entry_type="api",
            name="test-api",
            description="Test API",
            content='{"name": "updated"}',
            metadata={
                "method": "PUT",
                "url": "https://api.example.com/test/1",
                "headers": {},
            },
        )

        response = execute_api(entry)
        assert response is not None
        assert response.status_code == 200

    @responses.activate
    def test_makes_delete_request(self):
        """execute_api should make DELETE requests."""
        responses.add(
            responses.DELETE,
            "https://api.example.com/test/1",
            status=204,
        )

        entry = models.create_entry(
            entry_type="api",
            name="test-api",
            description="Test API",
            content="",
            metadata={
                "method": "DELETE",
                "url": "https://api.example.com/test/1",
                "headers": {},
            },
        )

        response = execute_api(entry)
        assert response is not None
        assert response.status_code == 204

    @responses.activate
    def test_sends_headers(self):
        """execute_api should send custom headers."""
        responses.add(
            responses.GET,
            "https://api.example.com/test",
            json={"success": True},
            status=200,
        )

        entry = models.create_entry(
            entry_type="api",
            name="test-api",
            description="Test API",
            content="",
            metadata={
                "method": "GET",
                "url": "https://api.example.com/test",
                "headers": {
                    "Authorization": "Bearer token123",
                    "X-Custom": "value",
                },
            },
        )

        response = execute_api(entry)
        assert response is not None
        # Verify headers were sent
        request = responses.calls[0].request
        assert request.headers["Authorization"] == "Bearer token123"
        assert request.headers["X-Custom"] == "value"

    def test_returns_none_for_missing_url(self):
        """execute_api should return None when URL is missing."""
        entry = models.create_entry(
            entry_type="api",
            name="test-api",
            description="Test API",
            content="",
            metadata={
                "method": "GET",
                "url": "",
                "headers": {},
            },
        )

        with patch("devvault.executor.print_error"):
            response = execute_api(entry)
            assert response is None

    @responses.activate
    def test_handles_non_json_body(self):
        """execute_api should handle non-JSON body content."""
        responses.add(
            responses.POST,
            "https://api.example.com/test",
            body="OK",
            status=200,
        )

        entry = models.create_entry(
            entry_type="api",
            name="test-api",
            description="Test API",
            content="plain text body",
            metadata={
                "method": "POST",
                "url": "https://api.example.com/test",
                "headers": {},
            },
        )

        response = execute_api(entry)
        assert response is not None

    @responses.activate
    def test_handles_request_exception(self):
        """execute_api should handle request exceptions."""
        import requests

        responses.add(
            responses.GET,
            "https://api.example.com/test",
            body=requests.exceptions.ConnectionError("Connection error"),
        )

        entry = models.create_entry(
            entry_type="api",
            name="test-api",
            description="Test API",
            content="",
            metadata={
                "method": "GET",
                "url": "https://api.example.com/test",
                "headers": {},
            },
        )

        with patch("devvault.executor.print_error"):
            response = execute_api(entry)
            assert response is None

    def test_defaults_to_get_method(self):
        """execute_api should default to GET method."""
        with responses.RequestsMock() as rsps:
            rsps.add(
                responses.GET,
                "https://api.example.com/test",
                json={"success": True},
                status=200,
            )

            entry = models.create_entry(
                entry_type="api",
                name="test-api",
                description="Test API",
                content="",
                metadata={
                    "url": "https://api.example.com/test",
                    "headers": {},
                },
            )

            response = execute_api(entry)
            assert response is not None
            assert rsps.calls[0].request.method == "GET"


class TestExecuteEntry:
    """Tests for execute_entry function."""

    def test_executes_command_entry(self):
        """execute_entry should execute command entries."""
        entry = models.create_entry(
            entry_type="command",
            name="test-cmd",
            description="Test command",
            content="echo hello",
        )

        with patch("devvault.executor.console") as mock_console:
            mock_console.input.return_value = "y"
            result = execute_entry(entry, confirm=True)
            assert result is True

    def test_skips_execution_on_cancel(self):
        """execute_entry should skip execution when user cancels."""
        entry = models.create_entry(
            entry_type="command",
            name="test-cmd",
            description="Test command",
            content="echo hello",
        )

        with patch("devvault.executor.console") as mock_console:
            mock_console.input.return_value = "n"
            result = execute_entry(entry, confirm=True)
            assert result is False

    def test_skips_confirmation_when_disabled(self):
        """execute_entry should skip confirmation when confirm=False."""
        entry = models.create_entry(
            entry_type="command",
            name="test-cmd",
            description="Test command",
            content="echo hello",
        )

        with patch("devvault.executor.console") as mock_console:
            result = execute_entry(entry, confirm=False)
            # Should not have called input for confirmation
            input_calls = [c for c in mock_console.input.call_args_list
                          if "Execute?" in str(c)]
            assert len(input_calls) == 0
            assert result is True

    def test_displays_snippet_content(self):
        """execute_entry should display snippet content without execution."""
        entry = models.create_entry(
            entry_type="snippet",
            name="test-snippet",
            description="Test snippet",
            content="def hello(): pass",
        )

        with patch("devvault.executor.console") as mock_console:
            result = execute_entry(entry, confirm=True)
            assert result is True
            # Should have printed the content
            print_calls = str(mock_console.print.call_args_list)
            assert "def hello()" in print_calls

    def test_displays_note_content(self):
        """execute_entry should display note content."""
        entry = models.create_entry(
            entry_type="note",
            name="test-note",
            description="Test note",
            content="This is a note",
        )

        with patch("devvault.executor.console") as mock_console:
            result = execute_entry(entry, confirm=True)
            assert result is True

    def test_displays_file_content(self):
        """execute_entry should display file content."""
        entry = models.create_entry(
            entry_type="file",
            name="test-file",
            description="Test file",
            content="config: value",
        )

        with patch("devvault.executor.console") as mock_console:
            result = execute_entry(entry, confirm=True)
            assert result is True

    def test_handles_playbook_entry(self):
        """execute_entry should handle playbook entries (not yet implemented)."""
        entry = models.create_entry(
            entry_type="playbook",
            name="test-playbook",
            description="Test playbook",
            content="step1\nstep2",
        )

        with patch("devvault.executor.console") as mock_console:
            result = execute_entry(entry, confirm=True)
            assert result is True  # Returns True but doesn't execute

    def test_handles_unknown_entry_type(self):
        """execute_entry should handle unknown entry types."""
        entry = {
            "type": "unknown",
            "name": "test",
            "content": "test",
        }

        with patch("devvault.executor.print_error") as mock_error:
            result = execute_entry(entry, confirm=True)
            assert result is False
            mock_error.assert_called()

    @responses.activate
    def test_executes_api_entry(self):
        """execute_entry should execute API entries."""
        responses.add(
            responses.GET,
            "https://api.example.com/test",
            json={"success": True},
            status=200,
        )

        entry = models.create_entry(
            entry_type="api",
            name="test-api",
            description="Test API",
            content="",
            metadata={
                "method": "GET",
                "url": "https://api.example.com/test",
                "headers": {},
            },
        )

        with patch("devvault.executor.console") as mock_console:
            mock_console.input.return_value = "y"
            result = execute_entry(entry, confirm=True)
            assert result is True


class TestVariableSubstitution:
    """Tests for variable substitution in execute_entry."""

    def test_prompts_for_variables(self, entry_with_variables):
        """execute_entry should prompt for variables."""
        with patch("devvault.executor.console") as mock_console:
            with patch("devvault.executor.prompt_for_variables") as mock_prompt:
                mock_prompt.return_value = {"USER": "admin", "HOST": "server.com"}
                mock_console.input.return_value = "y"

                execute_entry(entry_with_variables, confirm=True)

                mock_prompt.assert_called_once_with(["USER", "HOST"])

    def test_substitutes_variables_in_content(self, entry_with_variables):
        """execute_entry should substitute variables before execution."""
        with patch("devvault.executor.console") as mock_console:
            with patch("devvault.executor.prompt_for_variables") as mock_prompt:
                with patch("devvault.executor.execute_command") as mock_exec:
                    mock_prompt.return_value = {"USER": "admin", "HOST": "server.com"}
                    mock_console.input.return_value = "y"
                    mock_exec.return_value = (0, "", "")

                    execute_entry(entry_with_variables, confirm=True)

                    mock_exec.assert_called_once_with("ssh admin@server.com")

    def test_substitutes_variables_in_api_url(self):
        """execute_entry should substitute variables in API URLs."""
        # Include variable in content so prompt_for_variables is called
        entry = models.create_entry(
            entry_type="api",
            name="test-api",
            description="Test API",
            content="{{USER_ID}}",  # Include variable to trigger prompting
            metadata={
                "method": "GET",
                "url": "https://api.example.com/users/{{USER_ID}}",
                "headers": {},
            },
        )

        with responses.RequestsMock() as rsps:
            rsps.add(
                responses.GET,
                "https://api.example.com/users/123",
                json={"id": 123},
                status=200,
            )

            with patch("devvault.executor.console") as mock_console:
                with patch("devvault.executor.prompt_for_variables") as mock_prompt:
                    mock_prompt.return_value = {"USER_ID": "123"}
                    mock_console.input.return_value = "y"

                    result = execute_entry(entry, confirm=True)

                    assert result is True
                    assert rsps.calls[0].request.url == "https://api.example.com/users/123"


class TestExecutePlaybook:
    """Tests for execute_playbook function."""

    def test_executes_entries_in_order(self):
        """execute_playbook should execute entries in order."""
        entries = [
            models.create_entry(
                entry_type="command",
                name="step1",
                description="Step 1",
                content="echo step1",
            ),
            models.create_entry(
                entry_type="command",
                name="step2",
                description="Step 2",
                content="echo step2",
            ),
        ]

        with patch("devvault.executor.execute_entry") as mock_exec:
            mock_exec.return_value = True
            with patch("devvault.executor.console"):
                result = execute_playbook(entries)

                assert result is True
                assert mock_exec.call_count == 2
                # Verify order
                calls = mock_exec.call_args_list
                assert calls[0][0][0]["name"] == "step1"
                assert calls[1][0][0]["name"] == "step2"

    def test_stops_on_failure(self):
        """execute_playbook should stop when an entry fails."""
        entries = [
            models.create_entry(
                entry_type="command",
                name="step1",
                description="Step 1",
                content="echo step1",
            ),
            models.create_entry(
                entry_type="command",
                name="step2",
                description="Step 2",
                content="echo step2",
            ),
            models.create_entry(
                entry_type="command",
                name="step3",
                description="Step 3",
                content="echo step3",
            ),
        ]

        with patch("devvault.executor.execute_entry") as mock_exec:
            # First succeeds, second fails
            mock_exec.side_effect = [True, False, True]
            with patch("devvault.executor.console"):
                with patch("devvault.executor.print_error"):
                    result = execute_playbook(entries)

                    assert result is False
                    # Should have stopped after step2
                    assert mock_exec.call_count == 2

    def test_passes_confirm_false_to_entries(self):
        """execute_playbook should pass confirm=False to entries."""
        entries = [
            models.create_entry(
                entry_type="command",
                name="step1",
                description="Step 1",
                content="echo step1",
            ),
        ]

        with patch("devvault.executor.execute_entry") as mock_exec:
            mock_exec.return_value = True
            with patch("devvault.executor.console"):
                execute_playbook(entries)

                mock_exec.assert_called_with(entries[0], confirm=False)

    def test_handles_empty_playbook(self):
        """execute_playbook should handle empty playbook."""
        with patch("devvault.executor.console"):
            with patch("devvault.executor.print_success"):
                result = execute_playbook([])
                assert result is True
