# DevVault

Local-first knowledge base CLI for storing, organizing, and executing knowledge artifacts.

## Installation

```bash
pip install -e .
```

## Quick Start

```bash
# Initialize a vault in the current directory
devvault init

# Add a command
devvault add command -n "docker-clean" -d "Remove all containers" -c "docker rm -f \$(docker ps -aq)" -t docker,cleanup

# Add an API request
devvault add api -n "get-users" -d "Fetch all users" --method GET --url "https://api.example.com/users" -t api,users

# Add a code snippet
devvault add snippet -n "python-logger" -d "Standard logging setup" -c @logger.py -t python,logging

# Add a note
devvault add note -n "deploy-checklist" -d "Steps before deploy" -c "1. Run tests\n2. Update changelog"

# List all entries
devvault list

# Filter by type or tag
devvault list --type command
devvault list -t docker

# Search entries
devvault search "docker"

# View entry details
devvault show docker-clean

# Execute a command or API request
devvault run docker-clean
devvault run docker-clean --yes  # Skip confirmation

# Edit an entry
devvault edit docker-clean

# Delete an entry
devvault delete docker-clean

# List all tags
devvault tags

# Export/import entries
devvault export docker-clean -o backup.json
devvault import backup.json
```

## Entry Types

- **command**: Shell commands
- **api**: HTTP API requests
- **snippet**: Code snippets
- **file**: Configuration files
- **playbook**: Sequential command execution
- **note**: Text notes

## Variable Substitution

Use `{{VAR}}` placeholders in content - you'll be prompted for values at runtime:

```bash
devvault add command -n "ssh-server" -d "SSH to server" -c "ssh {{USER}}@{{HOST}}" -t ssh
devvault run ssh-server
# Prompts: Enter value for {{USER}}: ...
```

## Storage

All entries are stored in `data/vault.json` as JSON documents. This file is git-friendly and can be version controlled.
