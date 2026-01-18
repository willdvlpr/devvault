"""Entry models and schemas for devvault."""

import uuid
from datetime import datetime
from typing import Any


ENTRY_TYPES = ["command", "api", "snippet", "file", "playbook", "note"]


def generate_id() -> str:
    """Generate a unique ID for an entry."""
    return str(uuid.uuid4())[:8]


def create_entry(
    entry_type: str,
    name: str,
    description: str,
    content: str,
    tags: list[str] | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create a new entry document."""
    if entry_type not in ENTRY_TYPES:
        raise ValueError(f"Invalid entry type: {entry_type}. Must be one of {ENTRY_TYPES}")

    now = datetime.utcnow().isoformat()
    return {
        "id": generate_id(),
        "type": entry_type,
        "name": name,
        "description": description,
        "content": content,
        "tags": tags or [],
        "created_at": now,
        "updated_at": now,
        "metadata": metadata or {},
    }


def update_entry(entry: dict[str, Any], **updates) -> dict[str, Any]:
    """Update an entry with new values."""
    allowed_fields = {"name", "description", "content", "tags", "metadata"}
    for key, value in updates.items():
        if key in allowed_fields and value is not None:
            entry[key] = value
    entry["updated_at"] = datetime.utcnow().isoformat()
    return entry
