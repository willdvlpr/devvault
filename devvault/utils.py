"""Utility functions for devvault."""

import re
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table


console = Console()


def format_entry_table(entries: list[dict[str, Any]]) -> Table:
    """Format entries as a rich table."""
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("ID", style="dim", width=10)
    table.add_column("Type", width=10)
    table.add_column("Name", style="green")
    table.add_column("Description")
    table.add_column("Tags", style="yellow")

    for entry in entries:
        table.add_row(
            entry["id"],
            entry["type"],
            entry["name"],
            entry.get("description", "")[:50],
            ", ".join(entry.get("tags", [])),
        )

    return table


def format_entry_detail(entry: dict[str, Any]) -> Panel:
    """Format a single entry for detailed display."""
    content_lines = [
        f"[bold cyan]ID:[/] {entry['id']}",
        f"[bold cyan]Type:[/] {entry['type']}",
        f"[bold cyan]Name:[/] {entry['name']}",
        f"[bold cyan]Description:[/] {entry.get('description', '')}",
        f"[bold cyan]Tags:[/] {', '.join(entry.get('tags', []))}",
        f"[bold cyan]Created:[/] {entry.get('created_at', '')}",
        f"[bold cyan]Updated:[/] {entry.get('updated_at', '')}",
        "",
        "[bold cyan]Content:[/]",
    ]

    # Format content with syntax highlighting if possible
    content = entry.get("content", "")
    entry_type = entry["type"]

    # Add metadata for API entries
    if entry_type == "api":
        metadata = entry.get("metadata", {})
        method = metadata.get("method", "GET")
        url = metadata.get("url", "")
        headers = metadata.get("headers", {})
        content_lines.insert(7, f"[bold cyan]Method:[/] {method}")
        content_lines.insert(8, f"[bold cyan]URL:[/] {url}")
        if headers:
            content_lines.insert(9, f"[bold cyan]Headers:[/] {headers}")

    detail_text = "\n".join(content_lines)

    return Panel(
        f"{detail_text}\n{content}",
        title=f"[bold]{entry['name']}[/]",
        border_style="blue",
    )


def get_syntax_lexer(entry_type: str, content: str) -> str | None:
    """Determine syntax highlighting lexer based on entry type and content."""
    lexer_map = {
        "command": "bash",
        "snippet": None,  # Auto-detect or specified
        "api": "json",
    }

    if entry_type == "snippet":
        # Try to detect language from content
        if content.strip().startswith(("def ", "class ", "import ", "from ")):
            return "python"
        if content.strip().startswith(("function ", "const ", "let ", "var ")):
            return "javascript"
        if content.strip().startswith(("<", "<!DOCTYPE")):
            return "html"

    return lexer_map.get(entry_type)


def extract_variables(content: str) -> list[str]:
    """Extract {{VAR}} placeholders from content."""
    pattern = r"\{\{(\w+)\}\}"
    return re.findall(pattern, content)


def substitute_variables(content: str, variables: dict[str, str]) -> str:
    """Replace {{VAR}} placeholders with values."""
    result = content
    for var, value in variables.items():
        result = result.replace(f"{{{{{var}}}}}", value)
    return result


def prompt_for_variables(variables: list[str]) -> dict[str, str]:
    """Prompt user for variable values."""
    values = {}
    for var in variables:
        value = console.input(f"[yellow]Enter value for {{{{{var}}}}}:[/] ")
        values[var] = value
    return values


def print_success(message: str) -> None:
    """Print a success message."""
    console.print(f"[green]{message}[/]")


def print_error(message: str) -> None:
    """Print an error message."""
    console.print(f"[red]Error: {message}[/]")


def print_warning(message: str) -> None:
    """Print a warning message."""
    console.print(f"[yellow]Warning: {message}[/]")


def confirm(message: str) -> bool:
    """Prompt for confirmation."""
    response = console.input(f"[yellow]{message} [y/N]:[/] ")
    return response.lower() in ("y", "yes")
