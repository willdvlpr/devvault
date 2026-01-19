"""Unit tests for devvault.models module."""

import re
from datetime import datetime
from unittest.mock import patch

import pytest

from devvault.models import (
    ENTRY_TYPES,
    create_entry,
    generate_id,
    update_entry,
)


class TestGenerateId:
    """Tests for generate_id function."""

    def test_returns_string(self):
        """generate_id should return a string."""
        result = generate_id()
        assert isinstance(result, str)

    def test_returns_8_characters(self):
        """generate_id should return exactly 8 characters."""
        result = generate_id()
        assert len(result) == 8

    def test_returns_valid_hex_characters(self):
        """generate_id should return valid hex characters."""
        result = generate_id()
        assert re.match(r"^[0-9a-f]{8}$", result)

    def test_generates_unique_ids(self):
        """generate_id should generate unique IDs."""
        ids = [generate_id() for _ in range(100)]
        assert len(set(ids)) == 100


class TestCreateEntry:
    """Tests for create_entry function."""

    def test_creates_command_entry(self):
        """create_entry should create a valid command entry."""
        entry = create_entry(
            entry_type="command",
            name="test-cmd",
            description="Test command",
            content="echo hello",
        )

        assert entry["type"] == "command"
        assert entry["name"] == "test-cmd"
        assert entry["description"] == "Test command"
        assert entry["content"] == "echo hello"
        assert entry["tags"] == []
        assert entry["metadata"] == {}
        assert "id" in entry
        assert "created_at" in entry
        assert "updated_at" in entry

    def test_creates_entry_with_tags(self):
        """create_entry should include provided tags."""
        entry = create_entry(
            entry_type="command",
            name="test",
            description="Test",
            content="test",
            tags=["tag1", "tag2"],
        )
        assert entry["tags"] == ["tag1", "tag2"]

    def test_creates_entry_with_metadata(self):
        """create_entry should include provided metadata."""
        metadata = {"language": "python", "version": "3.8"}
        entry = create_entry(
            entry_type="snippet",
            name="test",
            description="Test",
            content="print('hello')",
            metadata=metadata,
        )
        assert entry["metadata"] == metadata

    def test_creates_api_entry_with_metadata(self):
        """create_entry should create API entry with full metadata."""
        entry = create_entry(
            entry_type="api",
            name="get-user",
            description="Get user by ID",
            content="",
            metadata={
                "method": "GET",
                "url": "https://api.example.com/users/1",
                "headers": {"Accept": "application/json"},
            },
        )

        assert entry["type"] == "api"
        assert entry["metadata"]["method"] == "GET"
        assert entry["metadata"]["url"] == "https://api.example.com/users/1"
        assert entry["metadata"]["headers"]["Accept"] == "application/json"

    @pytest.mark.parametrize("entry_type", ENTRY_TYPES)
    def test_creates_all_valid_entry_types(self, entry_type):
        """create_entry should accept all valid entry types."""
        entry = create_entry(
            entry_type=entry_type,
            name="test",
            description="Test",
            content="content",
        )
        assert entry["type"] == entry_type

    def test_raises_error_for_invalid_entry_type(self):
        """create_entry should raise ValueError for invalid entry type."""
        with pytest.raises(ValueError) as exc_info:
            create_entry(
                entry_type="invalid",
                name="test",
                description="Test",
                content="content",
            )
        assert "Invalid entry type" in str(exc_info.value)
        assert "invalid" in str(exc_info.value)

    def test_sets_timestamps(self):
        """create_entry should set created_at and updated_at timestamps."""
        entry = create_entry(
            entry_type="command",
            name="test",
            description="Test",
            content="test",
        )

        # Timestamps should be valid ISO format
        created_at = datetime.fromisoformat(entry["created_at"])
        updated_at = datetime.fromisoformat(entry["updated_at"])

        assert created_at == updated_at
        assert isinstance(created_at, datetime)

    def test_timestamps_are_recent(self):
        """create_entry should set timestamps to current time."""
        before = datetime.utcnow()
        entry = create_entry(
            entry_type="command",
            name="test",
            description="Test",
            content="test",
        )
        after = datetime.utcnow()

        created_at = datetime.fromisoformat(entry["created_at"])
        assert before <= created_at <= after

    def test_generates_unique_id(self):
        """create_entry should generate a unique ID for each entry."""
        entry1 = create_entry(
            entry_type="command",
            name="test1",
            description="Test 1",
            content="test1",
        )
        entry2 = create_entry(
            entry_type="command",
            name="test2",
            description="Test 2",
            content="test2",
        )
        assert entry1["id"] != entry2["id"]

    def test_handles_empty_tags_as_none(self):
        """create_entry should handle None tags."""
        entry = create_entry(
            entry_type="command",
            name="test",
            description="Test",
            content="test",
            tags=None,
        )
        assert entry["tags"] == []

    def test_handles_empty_metadata_as_none(self):
        """create_entry should handle None metadata."""
        entry = create_entry(
            entry_type="command",
            name="test",
            description="Test",
            content="test",
            metadata=None,
        )
        assert entry["metadata"] == {}


class TestUpdateEntry:
    """Tests for update_entry function."""

    def test_updates_name(self):
        """update_entry should update the name field."""
        entry = create_entry(
            entry_type="command",
            name="original",
            description="Test",
            content="test",
        )
        updated = update_entry(entry, name="updated")
        assert updated["name"] == "updated"

    def test_updates_description(self):
        """update_entry should update the description field."""
        entry = create_entry(
            entry_type="command",
            name="test",
            description="original",
            content="test",
        )
        updated = update_entry(entry, description="updated description")
        assert updated["description"] == "updated description"

    def test_updates_content(self):
        """update_entry should update the content field."""
        entry = create_entry(
            entry_type="command",
            name="test",
            description="Test",
            content="original",
        )
        updated = update_entry(entry, content="updated content")
        assert updated["content"] == "updated content"

    def test_updates_tags(self):
        """update_entry should update the tags field."""
        entry = create_entry(
            entry_type="command",
            name="test",
            description="Test",
            content="test",
            tags=["old"],
        )
        updated = update_entry(entry, tags=["new", "tags"])
        assert updated["tags"] == ["new", "tags"]

    def test_updates_metadata(self):
        """update_entry should update the metadata field."""
        entry = create_entry(
            entry_type="snippet",
            name="test",
            description="Test",
            content="test",
            metadata={"language": "python"},
        )
        updated = update_entry(entry, metadata={"language": "javascript"})
        assert updated["metadata"] == {"language": "javascript"}

    def test_updates_multiple_fields(self):
        """update_entry should update multiple fields at once."""
        entry = create_entry(
            entry_type="command",
            name="test",
            description="Test",
            content="test",
        )
        updated = update_entry(
            entry,
            name="new-name",
            description="New description",
            content="new content",
        )
        assert updated["name"] == "new-name"
        assert updated["description"] == "New description"
        assert updated["content"] == "new content"

    def test_ignores_disallowed_fields(self):
        """update_entry should ignore updates to protected fields."""
        entry = create_entry(
            entry_type="command",
            name="test",
            description="Test",
            content="test",
        )
        original_id = entry["id"]
        original_type = entry["type"]
        original_created = entry["created_at"]

        updated = update_entry(
            entry,
            id="new-id",
            type="api",
            created_at="2000-01-01T00:00:00",
        )

        assert updated["id"] == original_id
        assert updated["type"] == original_type
        assert updated["created_at"] == original_created

    def test_updates_updated_at_timestamp(self):
        """update_entry should update the updated_at timestamp."""
        entry = create_entry(
            entry_type="command",
            name="test",
            description="Test",
            content="test",
        )
        original_updated_at = entry["updated_at"]

        # Small delay to ensure timestamp changes
        import time
        time.sleep(0.01)

        updated = update_entry(entry, name="new-name")
        assert updated["updated_at"] != original_updated_at
        assert updated["updated_at"] > original_updated_at

    def test_ignores_none_values(self):
        """update_entry should not update fields with None values."""
        entry = create_entry(
            entry_type="command",
            name="test",
            description="Test",
            content="test",
        )
        updated = update_entry(entry, name=None, description=None)
        assert updated["name"] == "test"
        assert updated["description"] == "Test"

    def test_modifies_entry_in_place(self):
        """update_entry should modify the entry in place and return it."""
        entry = create_entry(
            entry_type="command",
            name="test",
            description="Test",
            content="test",
        )
        result = update_entry(entry, name="new-name")
        assert result is entry
        assert entry["name"] == "new-name"


class TestEntryTypes:
    """Tests for ENTRY_TYPES constant."""

    def test_contains_expected_types(self):
        """ENTRY_TYPES should contain all expected types."""
        expected = ["command", "api", "snippet", "file", "playbook", "note"]
        for entry_type in expected:
            assert entry_type in ENTRY_TYPES

    def test_has_correct_count(self):
        """ENTRY_TYPES should have exactly 6 types."""
        assert len(ENTRY_TYPES) == 6
