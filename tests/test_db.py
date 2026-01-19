"""Unit tests for devvault.db module."""

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from devvault import db, models


class TestGetVaultPath:
    """Tests for get_vault_path function."""

    def test_returns_path_object(self, temp_dir):
        """get_vault_path should return a Path object."""
        original_cwd = os.getcwd()
        try:
            os.chdir(temp_dir)
            result = db.get_vault_path()
            assert isinstance(result, Path)
        finally:
            os.chdir(original_cwd)

    def test_returns_correct_path(self, temp_dir):
        """get_vault_path should return path to vault.json in data directory."""
        original_cwd = os.getcwd()
        try:
            os.chdir(temp_dir)
            result = db.get_vault_path()
            # Use resolve() to handle macOS /var -> /private/var symlink
            assert result.resolve() == (temp_dir / "data" / "vault.json").resolve()
        finally:
            os.chdir(original_cwd)


class TestVaultExists:
    """Tests for vault_exists function."""

    def test_returns_false_when_no_vault(self, temp_dir):
        """vault_exists should return False when vault doesn't exist."""
        original_cwd = os.getcwd()
        try:
            os.chdir(temp_dir)
            assert db.vault_exists() is False
        finally:
            os.chdir(original_cwd)

    def test_returns_true_when_vault_exists(self, vault_dir):
        """vault_exists should return True when vault exists."""
        assert db.vault_exists() is True


class TestInitVault:
    """Tests for init_vault function."""

    def test_creates_data_directory(self, temp_dir):
        """init_vault should create the data directory."""
        original_cwd = os.getcwd()
        try:
            os.chdir(temp_dir)
            db.init_vault()
            assert (temp_dir / "data").is_dir()
        finally:
            os.chdir(original_cwd)

    def test_creates_vault_file(self, temp_dir):
        """init_vault should create the vault.json file."""
        original_cwd = os.getcwd()
        try:
            os.chdir(temp_dir)
            db.init_vault()
            assert (temp_dir / "data" / "vault.json").is_file()
        finally:
            os.chdir(original_cwd)

    def test_returns_vault_path(self, temp_dir):
        """init_vault should return the path to the vault file."""
        original_cwd = os.getcwd()
        try:
            os.chdir(temp_dir)
            result = db.init_vault()
            # Use resolve() to handle macOS /var -> /private/var symlink
            assert result.resolve() == (temp_dir / "data" / "vault.json").resolve()
        finally:
            os.chdir(original_cwd)

    def test_idempotent(self, temp_dir):
        """init_vault should be idempotent."""
        original_cwd = os.getcwd()
        try:
            os.chdir(temp_dir)
            db.init_vault()
            db.init_vault()  # Should not raise
            assert db.vault_exists()
        finally:
            os.chdir(original_cwd)


class TestGetDb:
    """Tests for get_db function."""

    def test_raises_when_no_vault(self, temp_dir):
        """get_db should raise FileNotFoundError when vault doesn't exist."""
        original_cwd = os.getcwd()
        try:
            os.chdir(temp_dir)
            with pytest.raises(FileNotFoundError) as exc_info:
                db.get_db()
            assert "No vault found" in str(exc_info.value)
        finally:
            os.chdir(original_cwd)

    def test_returns_tinydb_instance(self, vault_dir):
        """get_db should return a TinyDB instance."""
        from tinydb import TinyDB
        result = db.get_db()
        try:
            assert isinstance(result, TinyDB)
        finally:
            result.close()


class TestInsertEntry:
    """Tests for insert_entry function."""

    def test_inserts_entry(self, vault_dir, sample_command_entry):
        """insert_entry should insert an entry into the vault."""
        db.insert_entry(sample_command_entry)
        entries = db.get_all_entries()
        assert len(entries) == 1
        assert entries[0]["name"] == sample_command_entry["name"]

    def test_returns_document_id(self, vault_dir, sample_command_entry):
        """insert_entry should return the document ID."""
        result = db.insert_entry(sample_command_entry)
        assert isinstance(result, int)
        assert result > 0

    def test_inserts_multiple_entries(self, vault_dir, sample_command_entry, sample_api_entry):
        """insert_entry should allow inserting multiple entries."""
        db.insert_entry(sample_command_entry)
        db.insert_entry(sample_api_entry)
        entries = db.get_all_entries()
        assert len(entries) == 2


class TestGetEntryById:
    """Tests for get_entry_by_id function."""

    def test_returns_entry_by_id(self, vault_dir, sample_command_entry):
        """get_entry_by_id should return the entry with matching ID."""
        db.insert_entry(sample_command_entry)
        result = db.get_entry_by_id(sample_command_entry["id"])
        assert result is not None
        assert result["id"] == sample_command_entry["id"]

    def test_returns_none_for_nonexistent_id(self, vault_dir):
        """get_entry_by_id should return None for nonexistent ID."""
        result = db.get_entry_by_id("nonexistent")
        assert result is None

    def test_returns_correct_entry_with_multiple(self, vault_dir, sample_command_entry, sample_api_entry):
        """get_entry_by_id should return the correct entry when multiple exist."""
        db.insert_entry(sample_command_entry)
        db.insert_entry(sample_api_entry)

        result = db.get_entry_by_id(sample_api_entry["id"])
        assert result["name"] == sample_api_entry["name"]


class TestGetEntryByName:
    """Tests for get_entry_by_name function."""

    def test_returns_entry_by_name(self, vault_dir, sample_command_entry):
        """get_entry_by_name should return the entry with matching name."""
        db.insert_entry(sample_command_entry)
        result = db.get_entry_by_name(sample_command_entry["name"])
        assert result is not None
        assert result["name"] == sample_command_entry["name"]

    def test_returns_none_for_nonexistent_name(self, vault_dir):
        """get_entry_by_name should return None for nonexistent name."""
        result = db.get_entry_by_name("nonexistent")
        assert result is None

    def test_exact_match_only(self, vault_dir, sample_command_entry):
        """get_entry_by_name should require exact match."""
        db.insert_entry(sample_command_entry)
        result = db.get_entry_by_name("list")  # Partial match
        assert result is None


class TestGetEntry:
    """Tests for get_entry function."""

    def test_finds_by_id(self, vault_dir, sample_command_entry):
        """get_entry should find entry by ID."""
        db.insert_entry(sample_command_entry)
        result = db.get_entry(sample_command_entry["id"])
        assert result is not None
        assert result["id"] == sample_command_entry["id"]

    def test_finds_by_name(self, vault_dir, sample_command_entry):
        """get_entry should find entry by name."""
        db.insert_entry(sample_command_entry)
        result = db.get_entry(sample_command_entry["name"])
        assert result is not None
        assert result["name"] == sample_command_entry["name"]

    def test_id_takes_priority(self, vault_dir):
        """get_entry should check ID before name."""
        # Create an entry with name that looks like an ID
        entry1 = models.create_entry(
            entry_type="command",
            name="abcd1234",
            description="Entry 1",
            content="echo 1",
        )
        # Create another entry with that as its ID (mock)
        entry2 = models.create_entry(
            entry_type="command",
            name="different-name",
            description="Entry 2",
            content="echo 2",
        )
        entry2["id"] = "abcd1234"

        db.insert_entry(entry1)
        db.insert_entry(entry2)

        # Looking up "abcd1234" should find entry2 by ID first
        result = db.get_entry("abcd1234")
        assert result["content"] == "echo 2"

    def test_returns_none_when_not_found(self, vault_dir):
        """get_entry should return None when entry not found."""
        result = db.get_entry("nonexistent")
        assert result is None


class TestGetAllEntries:
    """Tests for get_all_entries function."""

    def test_returns_empty_list_when_empty(self, vault_dir):
        """get_all_entries should return empty list for empty vault."""
        result = db.get_all_entries()
        assert result == []

    def test_returns_all_entries(self, populated_vault, sample_command_entry, sample_api_entry, sample_snippet_entry):
        """get_all_entries should return all entries in vault."""
        result = db.get_all_entries()
        assert len(result) == 3

    def test_returns_list(self, vault_dir):
        """get_all_entries should return a list."""
        result = db.get_all_entries()
        assert isinstance(result, list)


class TestGetEntriesByType:
    """Tests for get_entries_by_type function."""

    def test_returns_entries_of_type(self, populated_vault):
        """get_entries_by_type should return entries matching the type."""
        result = db.get_entries_by_type("command")
        assert len(result) == 1
        assert result[0]["type"] == "command"

    def test_returns_empty_for_no_matches(self, populated_vault):
        """get_entries_by_type should return empty list for no matches."""
        result = db.get_entries_by_type("playbook")
        assert result == []

    def test_returns_multiple_of_same_type(self, vault_dir):
        """get_entries_by_type should return all entries of the type."""
        entry1 = models.create_entry(
            entry_type="command",
            name="cmd1",
            description="Command 1",
            content="echo 1",
        )
        entry2 = models.create_entry(
            entry_type="command",
            name="cmd2",
            description="Command 2",
            content="echo 2",
        )
        db.insert_entry(entry1)
        db.insert_entry(entry2)

        result = db.get_entries_by_type("command")
        assert len(result) == 2


class TestGetEntriesByTag:
    """Tests for get_entries_by_tag function."""

    def test_returns_entries_with_tag(self, populated_vault):
        """get_entries_by_tag should return entries containing the tag."""
        result = db.get_entries_by_tag("shell")
        assert len(result) == 1
        assert "shell" in result[0]["tags"]

    def test_returns_empty_for_no_matches(self, populated_vault):
        """get_entries_by_tag should return empty list for no matches."""
        result = db.get_entries_by_tag("nonexistent-tag")
        assert result == []

    def test_returns_multiple_with_same_tag(self, vault_dir):
        """get_entries_by_tag should return all entries with the tag."""
        entry1 = models.create_entry(
            entry_type="command",
            name="cmd1",
            description="Command 1",
            content="echo 1",
            tags=["shared-tag", "unique1"],
        )
        entry2 = models.create_entry(
            entry_type="snippet",
            name="snippet1",
            description="Snippet 1",
            content="print(1)",
            tags=["shared-tag", "unique2"],
        )
        db.insert_entry(entry1)
        db.insert_entry(entry2)

        result = db.get_entries_by_tag("shared-tag")
        assert len(result) == 2


class TestSearchEntries:
    """Tests for search_entries function."""

    def test_searches_name(self, populated_vault):
        """search_entries should find matches in name."""
        result = db.search_entries("list-files")
        assert len(result) == 1
        assert result[0]["name"] == "list-files"

    def test_searches_description(self, populated_vault):
        """search_entries should find matches in description."""
        result = db.search_entries("Fetch all users")
        assert len(result) == 1
        assert result[0]["name"] == "get-users"

    def test_searches_content(self, populated_vault):
        """search_entries should find matches in content."""
        result = db.search_entries("Hello, World")
        assert len(result) == 1
        assert result[0]["name"] == "python-hello"

    def test_searches_tags(self, populated_vault):
        """search_entries should find matches in tags."""
        result = db.search_entries("filesystem")
        assert len(result) == 1
        assert "filesystem" in result[0]["tags"]

    def test_case_insensitive(self, populated_vault):
        """search_entries should be case insensitive."""
        result = db.search_entries("PYTHON")
        assert len(result) == 1
        assert result[0]["name"] == "python-hello"

    def test_partial_match(self, populated_vault):
        """search_entries should support partial matches."""
        result = db.search_entries("user")
        assert len(result) >= 1
        assert any(entry["name"] == "get-users" for entry in result)

    def test_returns_empty_for_no_matches(self, populated_vault):
        """search_entries should return empty list for no matches."""
        result = db.search_entries("xyznonexistent")
        assert result == []


class TestUpdateEntry:
    """Tests for update_entry function (db version)."""

    def test_updates_by_id(self, vault_dir, sample_command_entry):
        """update_entry should update entry by ID."""
        db.insert_entry(sample_command_entry)
        result = db.update_entry(
            sample_command_entry["id"],
            {"description": "Updated description"},
        )
        assert result is True

        entry = db.get_entry(sample_command_entry["id"])
        assert entry["description"] == "Updated description"

    def test_updates_by_name(self, vault_dir, sample_command_entry):
        """update_entry should update entry by name."""
        db.insert_entry(sample_command_entry)
        result = db.update_entry(
            sample_command_entry["name"],
            {"description": "Updated description"},
        )
        assert result is True

        entry = db.get_entry(sample_command_entry["name"])
        assert entry["description"] == "Updated description"

    def test_returns_false_when_not_found(self, vault_dir):
        """update_entry should return False when entry not found."""
        result = db.update_entry("nonexistent", {"description": "test"})
        assert result is False


class TestDeleteEntry:
    """Tests for delete_entry function."""

    def test_deletes_by_id(self, vault_dir, sample_command_entry):
        """delete_entry should delete entry by ID."""
        db.insert_entry(sample_command_entry)
        result = db.delete_entry(sample_command_entry["id"])
        assert result is True
        assert db.get_entry(sample_command_entry["id"]) is None

    def test_deletes_by_name(self, vault_dir, sample_command_entry):
        """delete_entry should delete entry by name."""
        db.insert_entry(sample_command_entry)
        result = db.delete_entry(sample_command_entry["name"])
        assert result is True
        assert db.get_entry(sample_command_entry["name"]) is None

    def test_returns_false_when_not_found(self, vault_dir):
        """delete_entry should return False when entry not found."""
        result = db.delete_entry("nonexistent")
        assert result is False

    def test_only_deletes_matching_entry(self, populated_vault):
        """delete_entry should only delete the matching entry."""
        entries_before = db.get_all_entries()
        assert len(entries_before) == 3

        db.delete_entry("list-files")

        entries_after = db.get_all_entries()
        assert len(entries_after) == 2
        assert not any(e["name"] == "list-files" for e in entries_after)


class TestGetAllTags:
    """Tests for get_all_tags function."""

    def test_returns_empty_for_empty_vault(self, vault_dir):
        """get_all_tags should return empty list for empty vault."""
        result = db.get_all_tags()
        assert result == []

    def test_returns_unique_tags(self, populated_vault):
        """get_all_tags should return unique tags."""
        result = db.get_all_tags()
        assert len(result) == len(set(result))

    def test_returns_sorted_tags(self, populated_vault):
        """get_all_tags should return sorted tags."""
        result = db.get_all_tags()
        assert result == sorted(result)

    def test_includes_all_tags(self, populated_vault):
        """get_all_tags should include tags from all entries."""
        result = db.get_all_tags()
        # From fixtures: shell, filesystem, api, users, python, example
        expected_tags = {"shell", "filesystem", "api", "users", "python", "example"}
        assert expected_tags.issubset(set(result))

    def test_handles_entries_without_tags(self, vault_dir):
        """get_all_tags should handle entries with no tags."""
        entry = models.create_entry(
            entry_type="command",
            name="no-tags",
            description="No tags",
            content="echo",
            tags=[],
        )
        db.insert_entry(entry)
        result = db.get_all_tags()
        assert result == []
