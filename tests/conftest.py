"""Pytest fixtures for devvault tests."""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from devvault import db, models


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def vault_dir(temp_dir):
    """Create a temporary vault directory and change to it."""
    original_cwd = os.getcwd()
    os.chdir(temp_dir)

    try:
        # Initialize vault
        db.init_vault()
        yield temp_dir
    finally:
        os.chdir(original_cwd)


@pytest.fixture
def sample_command_entry():
    """Create a sample command entry."""
    return models.create_entry(
        entry_type="command",
        name="list-files",
        description="List all files in directory",
        content="ls -la",
        tags=["shell", "filesystem"],
    )


@pytest.fixture
def sample_api_entry():
    """Create a sample API entry."""
    return models.create_entry(
        entry_type="api",
        name="get-users",
        description="Fetch all users from API",
        content='{"filter": "active"}',
        tags=["api", "users"],
        metadata={
            "method": "GET",
            "url": "https://api.example.com/users",
            "headers": {"Authorization": "Bearer {{TOKEN}}"},
        },
    )


@pytest.fixture
def sample_snippet_entry():
    """Create a sample snippet entry."""
    return models.create_entry(
        entry_type="snippet",
        name="python-hello",
        description="Hello world in Python",
        content='def hello():\n    print("Hello, World!")',
        tags=["python", "example"],
        metadata={"language": "python"},
    )


@pytest.fixture
def sample_note_entry():
    """Create a sample note entry."""
    return models.create_entry(
        entry_type="note",
        name="deployment-notes",
        description="Notes about deployment process",
        content="Remember to update the environment variables before deploying.",
        tags=["deployment", "notes"],
    )


@pytest.fixture
def sample_file_entry():
    """Create a sample file entry."""
    return models.create_entry(
        entry_type="file",
        name="docker-compose",
        description="Docker compose configuration",
        content="version: '3'\nservices:\n  app:\n    build: .",
        tags=["docker", "config"],
        metadata={"filename": "docker-compose.yml"},
    )


@pytest.fixture
def sample_playbook_entry():
    """Create a sample playbook entry."""
    return models.create_entry(
        entry_type="playbook",
        name="deploy-playbook",
        description="Deployment playbook",
        content="1. Build application\n2. Run tests\n3. Deploy to server",
        tags=["deployment", "playbook"],
    )


@pytest.fixture
def populated_vault(vault_dir, sample_command_entry, sample_api_entry, sample_snippet_entry):
    """Create a vault with sample entries."""
    db.insert_entry(sample_command_entry)
    db.insert_entry(sample_api_entry)
    db.insert_entry(sample_snippet_entry)
    return vault_dir


@pytest.fixture
def mock_console():
    """Mock the rich console for testing output functions."""
    with patch("devvault.utils.console") as mock:
        yield mock


@pytest.fixture
def entry_with_variables():
    """Create an entry with variable placeholders."""
    return models.create_entry(
        entry_type="command",
        name="ssh-connect",
        description="SSH into a server",
        content="ssh {{USER}}@{{HOST}}",
        tags=["ssh", "remote"],
    )
