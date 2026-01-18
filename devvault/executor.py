"""Execution engine for devvault entries."""

import json
import subprocess
from typing import Any

import requests

from .utils import (
    console,
    extract_variables,
    substitute_variables,
    prompt_for_variables,
    print_error,
    print_success,
)


def execute_command(content: str) -> tuple[int, str, str]:
    """Execute a shell command and return (return_code, stdout, stderr)."""
    result = subprocess.run(
        content,
        shell=True,
        capture_output=True,
        text=True,
    )
    return result.returncode, result.stdout, result.stderr


def execute_api(entry: dict[str, Any]) -> requests.Response | None:
    """Execute an API request."""
    metadata = entry.get("metadata", {})
    method = metadata.get("method", "GET").upper()
    url = metadata.get("url", "")
    headers = metadata.get("headers", {})
    content = entry.get("content", "")

    if not url:
        print_error("No URL specified for API request")
        return None

    # Parse body if provided
    body = None
    if content:
        try:
            body = json.loads(content)
        except json.JSONDecodeError:
            body = content

    try:
        response = requests.request(
            method=method,
            url=url,
            headers=headers,
            json=body if isinstance(body, dict) else None,
            data=body if isinstance(body, str) else None,
            timeout=30,
        )
        return response
    except requests.RequestException as e:
        print_error(f"Request failed: {e}")
        return None


def execute_playbook(entries: list[dict[str, Any]]) -> bool:
    """Execute a sequence of entries."""
    for i, entry in enumerate(entries, 1):
        console.print(f"\n[bold cyan]Step {i}/{len(entries)}:[/] {entry['name']}")
        success = execute_entry(entry, confirm=False)
        if not success:
            print_error(f"Playbook failed at step {i}")
            return False
    print_success("Playbook completed successfully")
    return True


def execute_entry(entry: dict[str, Any], confirm: bool = True) -> bool:
    """Execute an entry based on its type."""
    entry_type = entry["type"]
    content = entry.get("content", "")

    # Handle variable substitution
    variables = extract_variables(content)
    if variables:
        console.print(f"[yellow]This entry requires {len(variables)} variable(s):[/]")
        values = prompt_for_variables(variables)
        content = substitute_variables(content, values)

        # Also substitute in URL for API entries
        if entry_type == "api":
            url = entry.get("metadata", {}).get("url", "")
            url_vars = extract_variables(url)
            if url_vars:
                url = substitute_variables(url, values)
                entry["metadata"]["url"] = url

    if entry_type == "command":
        console.print(f"\n[bold]Command:[/] {content}")
        if confirm:
            response = console.input("[yellow]Execute? [y/N]:[/] ")
            if response.lower() not in ("y", "yes"):
                console.print("[dim]Cancelled[/]")
                return False

        console.print("\n[bold cyan]Output:[/]")
        returncode, stdout, stderr = execute_command(content)

        if stdout:
            console.print(stdout)
        if stderr:
            console.print(f"[red]{stderr}[/]")

        if returncode == 0:
            print_success(f"Command completed (exit code: {returncode})")
        else:
            print_error(f"Command failed (exit code: {returncode})")
        return returncode == 0

    elif entry_type == "api":
        metadata = entry.get("metadata", {})
        method = metadata.get("method", "GET")
        url = metadata.get("url", "")

        console.print(f"\n[bold]API Request:[/] {method} {url}")
        if content:
            console.print(f"[bold]Body:[/] {content[:200]}...")

        if confirm:
            response = console.input("[yellow]Execute? [y/N]:[/] ")
            if response.lower() not in ("y", "yes"):
                console.print("[dim]Cancelled[/]")
                return False

        response = execute_api(entry)
        if response:
            console.print(f"\n[bold cyan]Status:[/] {response.status_code}")
            console.print("[bold cyan]Response:[/]")
            try:
                console.print_json(response.text)
            except Exception:
                console.print(response.text)
            return response.ok
        return False

    elif entry_type == "snippet":
        console.print("\n[bold cyan]Snippet content:[/]")
        console.print(content)
        print_success("Snippet displayed (snippets are not executable)")
        return True

    elif entry_type == "note":
        console.print("\n[bold cyan]Note:[/]")
        console.print(content)
        return True

    elif entry_type == "file":
        console.print("\n[bold cyan]File content:[/]")
        console.print(content)
        return True

    elif entry_type == "playbook":
        # Playbook execution would need to parse content for entry references
        console.print("[yellow]Playbook execution not yet implemented[/]")
        console.print("[dim]Content:[/]")
        console.print(content)
        return True

    else:
        print_error(f"Unknown entry type: {entry_type}")
        return False
