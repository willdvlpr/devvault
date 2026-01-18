"""Main CLI entry point for devvault."""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import click

from . import db
from . import models
from .executor import execute_entry
from .utils import (
    console,
    format_entry_table,
    format_entry_detail,
    print_success,
    print_error,
    print_warning,
)


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """DevVault - Local-first knowledge base CLI."""
    pass


@cli.command()
def init():
    """Initialize a new vault in the current directory."""
    if db.vault_exists():
        print_warning("Vault already exists in this directory")
        return

    vault_path = db.init_vault()
    print_success(f"Vault initialized at {vault_path}")


@cli.group()
def add():
    """Add a new entry to the vault."""
    pass


def parse_tags(tags: str | None) -> list[str]:
    """Parse comma-separated tags string."""
    if not tags:
        return []
    return [t.strip() for t in tags.split(",") if t.strip()]


def read_content(content: str) -> str:
    """Read content from string or file if prefixed with @."""
    if content.startswith("@"):
        filepath = content[1:]
        try:
            return Path(filepath).read_text()
        except FileNotFoundError:
            print_error(f"File not found: {filepath}")
            sys.exit(1)
    return content


@add.command("command")
@click.option("-n", "--name", required=True, help="Short identifier")
@click.option("-d", "--description", required=True, help="What it does")
@click.option("-c", "--content", required=True, help="Command string (use @file to read from file)")
@click.option("-t", "--tags", help="Comma-separated tags")
def add_command(name: str, description: str, content: str, tags: str | None):
    """Add a command entry."""
    content = read_content(content)
    entry = models.create_entry(
        entry_type="command",
        name=name,
        description=description,
        content=content,
        tags=parse_tags(tags),
    )
    db.insert_entry(entry)
    print_success(f"Added command '{name}' (ID: {entry['id']})")


@add.command("api")
@click.option("-n", "--name", required=True, help="Short identifier")
@click.option("-d", "--description", required=True, help="What it does")
@click.option("--method", default="GET", help="HTTP method")
@click.option("--url", required=True, help="API URL")
@click.option("--header", "-H", multiple=True, help="Headers (format: Key:Value)")
@click.option("-c", "--content", default="", help="Request body (use @file to read from file)")
@click.option("-t", "--tags", help="Comma-separated tags")
def add_api(name: str, description: str, method: str, url: str, header: tuple, content: str, tags: str | None):
    """Add an API request entry."""
    if content:
        content = read_content(content)

    # Parse headers
    headers = {}
    for h in header:
        if ":" in h:
            key, value = h.split(":", 1)
            headers[key.strip()] = value.strip()

    entry = models.create_entry(
        entry_type="api",
        name=name,
        description=description,
        content=content,
        tags=parse_tags(tags),
        metadata={"method": method.upper(), "url": url, "headers": headers},
    )
    db.insert_entry(entry)
    print_success(f"Added API request '{name}' (ID: {entry['id']})")


@add.command("snippet")
@click.option("-n", "--name", required=True, help="Short identifier")
@click.option("-d", "--description", required=True, help="What it does")
@click.option("-c", "--content", required=True, help="Code content (use @file to read from file)")
@click.option("-t", "--tags", help="Comma-separated tags")
@click.option("-l", "--language", help="Programming language")
def add_snippet(name: str, description: str, content: str, tags: str | None, language: str | None):
    """Add a code snippet entry."""
    content = read_content(content)
    metadata = {}
    if language:
        metadata["language"] = language

    entry = models.create_entry(
        entry_type="snippet",
        name=name,
        description=description,
        content=content,
        tags=parse_tags(tags),
        metadata=metadata,
    )
    db.insert_entry(entry)
    print_success(f"Added snippet '{name}' (ID: {entry['id']})")


@add.command("note")
@click.option("-n", "--name", required=True, help="Short identifier")
@click.option("-d", "--description", required=True, help="What it does")
@click.option("-c", "--content", required=True, help="Note content (use @file to read from file)")
@click.option("-t", "--tags", help="Comma-separated tags")
def add_note(name: str, description: str, content: str, tags: str | None):
    """Add a note entry."""
    content = read_content(content)
    entry = models.create_entry(
        entry_type="note",
        name=name,
        description=description,
        content=content,
        tags=parse_tags(tags),
    )
    db.insert_entry(entry)
    print_success(f"Added note '{name}' (ID: {entry['id']})")


@add.command("file")
@click.option("-n", "--name", required=True, help="Short identifier")
@click.option("-d", "--description", required=True, help="What it does")
@click.option("-c", "--content", required=True, help="File content (use @file to read from file)")
@click.option("-t", "--tags", help="Comma-separated tags")
@click.option("-f", "--filename", help="Original filename")
def add_file(name: str, description: str, content: str, tags: str | None, filename: str | None):
    """Add a file entry."""
    content = read_content(content)
    metadata = {}
    if filename:
        metadata["filename"] = filename

    entry = models.create_entry(
        entry_type="file",
        name=name,
        description=description,
        content=content,
        tags=parse_tags(tags),
        metadata=metadata,
    )
    db.insert_entry(entry)
    print_success(f"Added file '{name}' (ID: {entry['id']})")


@add.command("playbook")
@click.option("-n", "--name", required=True, help="Short identifier")
@click.option("-d", "--description", required=True, help="What it does")
@click.option("-c", "--content", required=True, help="Playbook content (use @file to read from file)")
@click.option("-t", "--tags", help="Comma-separated tags")
def add_playbook(name: str, description: str, content: str, tags: str | None):
    """Add a playbook entry."""
    content = read_content(content)
    entry = models.create_entry(
        entry_type="playbook",
        name=name,
        description=description,
        content=content,
        tags=parse_tags(tags),
    )
    db.insert_entry(entry)
    print_success(f"Added playbook '{name}' (ID: {entry['id']})")


@cli.command("list")
@click.option("--type", "entry_type", help="Filter by entry type")
@click.option("-t", "--tag", help="Filter by tag")
def list_entries(entry_type: str | None, tag: str | None):
    """List all entries."""
    try:
        if entry_type:
            entries = db.get_entries_by_type(entry_type)
        elif tag:
            entries = db.get_entries_by_tag(tag)
        else:
            entries = db.get_all_entries()

        if not entries:
            console.print("[dim]No entries found[/]")
            return

        table = format_entry_table(entries)
        console.print(table)
    except FileNotFoundError as e:
        print_error(str(e))


@cli.command()
@click.argument("query")
def search(query: str):
    """Full-text search across entries."""
    try:
        entries = db.search_entries(query)
        if not entries:
            console.print(f"[dim]No entries found matching '{query}'[/]")
            return

        table = format_entry_table(entries)
        console.print(table)
    except FileNotFoundError as e:
        print_error(str(e))


@cli.command()
@click.argument("identifier")
def show(identifier: str):
    """View entry details."""
    try:
        entry = db.get_entry(identifier)
        if not entry:
            print_error(f"Entry not found: {identifier}")
            return

        panel = format_entry_detail(entry)
        console.print(panel)
    except FileNotFoundError as e:
        print_error(str(e))


@cli.command()
@click.argument("identifier")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation")
def run(identifier: str, yes: bool):
    """Execute a command or API request."""
    try:
        entry = db.get_entry(identifier)
        if not entry:
            print_error(f"Entry not found: {identifier}")
            return

        execute_entry(entry, confirm=not yes)
    except FileNotFoundError as e:
        print_error(str(e))


@cli.command()
@click.argument("identifier")
def edit(identifier: str):
    """Edit an entry in $EDITOR."""
    try:
        entry = db.get_entry(identifier)
        if not entry:
            print_error(f"Entry not found: {identifier}")
            return

        editor = os.environ.get("EDITOR", "vim")

        # Create temp file with entry as JSON
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(entry, f, indent=2)
            temp_path = f.name

        # Open in editor
        subprocess.run([editor, temp_path])

        # Read back and update
        try:
            with open(temp_path) as f:
                updated = json.load(f)

            # Update the entry
            updated["updated_at"] = models.update_entry(entry)["updated_at"]
            db.update_entry(identifier, updated)
            print_success(f"Updated entry '{entry['name']}'")
        except json.JSONDecodeError:
            print_error("Invalid JSON in edited file")
        finally:
            os.unlink(temp_path)

    except FileNotFoundError as e:
        print_error(str(e))


@cli.command()
@click.argument("identifier")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation")
def delete(identifier: str, yes: bool):
    """Delete an entry."""
    try:
        entry = db.get_entry(identifier)
        if not entry:
            print_error(f"Entry not found: {identifier}")
            return

        if not yes:
            response = console.input(f"[yellow]Delete '{entry['name']}'? [y/N]:[/] ")
            if response.lower() not in ("y", "yes"):
                console.print("[dim]Cancelled[/]")
                return

        db.delete_entry(identifier)
        print_success(f"Deleted entry '{entry['name']}'")
    except FileNotFoundError as e:
        print_error(str(e))


@cli.command()
def tags():
    """List all tags."""
    try:
        all_tags = db.get_all_tags()
        if not all_tags:
            console.print("[dim]No tags found[/]")
            return

        console.print("[bold]Tags:[/]")
        for tag in all_tags:
            console.print(f"  - {tag}")
    except FileNotFoundError as e:
        print_error(str(e))


@cli.command("export")
@click.argument("identifier")
@click.option("-o", "--output", required=True, help="Output file path")
def export_entry(identifier: str, output: str):
    """Export an entry to a file."""
    try:
        entry = db.get_entry(identifier)
        if not entry:
            print_error(f"Entry not found: {identifier}")
            return

        with open(output, "w") as f:
            json.dump(entry, f, indent=2)

        print_success(f"Exported '{entry['name']}' to {output}")
    except FileNotFoundError as e:
        print_error(str(e))


@cli.command("import")
@click.argument("filepath")
def import_entry(filepath: str):
    """Import an entry from a JSON file."""
    try:
        with open(filepath) as f:
            entry = json.load(f)

        # Validate required fields
        required = ["type", "name", "description", "content"]
        for field in required:
            if field not in entry:
                print_error(f"Missing required field: {field}")
                return

        # Generate new ID and timestamps if importing
        entry["id"] = models.generate_id()
        from datetime import datetime
        now = datetime.utcnow().isoformat()
        entry["created_at"] = now
        entry["updated_at"] = now

        db.insert_entry(entry)
        print_success(f"Imported '{entry['name']}' (ID: {entry['id']})")
    except json.JSONDecodeError:
        print_error("Invalid JSON file")
    except FileNotFoundError:
        print_error(f"File not found: {filepath}")


if __name__ == "__main__":
    cli()
