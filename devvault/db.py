"""TinyDB database layer for devvault."""

import os
from pathlib import Path
from typing import Any

from tinydb import TinyDB, Query


VAULT_DIR = "data"
VAULT_FILE = "vault.json"


def get_vault_path() -> Path:
    """Get the path to the vault database file."""
    return Path.cwd() / VAULT_DIR / VAULT_FILE


def vault_exists() -> bool:
    """Check if a vault has been initialized in the current directory."""
    return get_vault_path().exists()


def init_vault() -> Path:
    """Initialize a new vault in the current directory."""
    vault_dir = Path.cwd() / VAULT_DIR
    vault_dir.mkdir(exist_ok=True)
    vault_path = vault_dir / VAULT_FILE

    # Create empty database
    db = TinyDB(vault_path)
    db.close()

    return vault_path


def get_db() -> TinyDB:
    """Get a connection to the vault database."""
    vault_path = get_vault_path()
    if not vault_path.exists():
        raise FileNotFoundError(
            "No vault found. Run 'devvault init' to create one."
        )
    return TinyDB(vault_path)


def insert_entry(entry: dict[str, Any]) -> int:
    """Insert a new entry into the vault."""
    db = get_db()
    try:
        return db.insert(entry)
    finally:
        db.close()


def get_entry_by_id(entry_id: str) -> dict[str, Any] | None:
    """Get an entry by its ID."""
    db = get_db()
    try:
        Entry = Query()
        result = db.search(Entry.id == entry_id)
        return result[0] if result else None
    finally:
        db.close()


def get_entry_by_name(name: str) -> dict[str, Any] | None:
    """Get an entry by its name."""
    db = get_db()
    try:
        Entry = Query()
        result = db.search(Entry.name == name)
        return result[0] if result else None
    finally:
        db.close()


def get_entry(identifier: str) -> dict[str, Any] | None:
    """Get an entry by ID or name."""
    entry = get_entry_by_id(identifier)
    if entry:
        return entry
    return get_entry_by_name(identifier)


def get_all_entries() -> list[dict[str, Any]]:
    """Get all entries from the vault."""
    db = get_db()
    try:
        return db.all()
    finally:
        db.close()


def get_entries_by_type(entry_type: str) -> list[dict[str, Any]]:
    """Get all entries of a specific type."""
    db = get_db()
    try:
        Entry = Query()
        return db.search(Entry.type == entry_type)
    finally:
        db.close()


def get_entries_by_tag(tag: str) -> list[dict[str, Any]]:
    """Get all entries with a specific tag."""
    db = get_db()
    try:
        Entry = Query()
        return db.search(Entry.tags.any([tag]))
    finally:
        db.close()


def search_entries(query: str) -> list[dict[str, Any]]:
    """Full-text search across name, description, content, and tags."""
    db = get_db()
    try:
        query_lower = query.lower()
        results = []
        for entry in db.all():
            searchable = " ".join([
                entry.get("name", ""),
                entry.get("description", ""),
                entry.get("content", ""),
                " ".join(entry.get("tags", [])),
            ]).lower()
            if query_lower in searchable:
                results.append(entry)
        return results
    finally:
        db.close()


def update_entry(identifier: str, updates: dict[str, Any]) -> bool:
    """Update an entry by ID or name."""
    db = get_db()
    try:
        Entry = Query()
        # Try by ID first
        result = db.update(updates, Entry.id == identifier)
        if result:
            return True
        # Try by name
        result = db.update(updates, Entry.name == identifier)
        return bool(result)
    finally:
        db.close()


def delete_entry(identifier: str) -> bool:
    """Delete an entry by ID or name."""
    db = get_db()
    try:
        Entry = Query()
        # Try by ID first
        result = db.remove(Entry.id == identifier)
        if result:
            return True
        # Try by name
        result = db.remove(Entry.name == identifier)
        return bool(result)
    finally:
        db.close()


def get_all_tags() -> list[str]:
    """Get all unique tags from the vault."""
    db = get_db()
    try:
        tags = set()
        for entry in db.all():
            tags.update(entry.get("tags", []))
        return sorted(tags)
    finally:
        db.close()
