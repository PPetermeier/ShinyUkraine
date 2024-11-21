# VSCode Refactoring Guide for Ukraine Support Tracker

## Step 1: Create Migration Helper

```python
# migration_helper.py
"""Helper module to assist with code migration to new patterns."""

from typing import Dict, Set

# Track which files have been migrated
MIGRATED_FILES: Set[str] = set()

# Map old imports to new ones
IMPORT_MAPPINGS: Dict[str, str] = {
    'AID_TYPES_COLUMNS': 'AidCategory',
    'TOTAL_SUPPORT_COLUMNS': 'TableNames',
    'COUNTRY_AID_COLUMNS': 'TableNames',
    'MAP_SUPPORT_TYPES': 'AidCategory',
}

# Add TODO comments for migration
MIGRATION_TODO = """
# TODO: Migration needed
# - Replace string constants with enums
# - Add type hints
# - Update docstrings
"""

def add_migration_todo(filename: str) -> None:
    """Add migration TODO comment to file."""
    with open(filename, 'r+') as f:
        content = f.read()
        if MIGRATION_TODO not in content:
            f.seek(0, 0)
            f.write(MIGRATION_TODO + '\n' + content)

def mark_file_migrated(filename: str) -> None:
    """Mark a file as successfully migrated."""
    MIGRATED_FILES.add(filename)
```

## Step 2: Install Helpful VSCode Extensions

1. **Python Extensions:**
   - Python (Microsoft)
   - Python Type Hint
   - Pylance
   - Python Indent
   - autoDocstring

2. **Refactoring Helpers:**
   - Better Comments
   - Todo Tree
   - Git Lens
   - Import Cost

## Step 3: Create VSCode Tasks

Create `.vscode/tasks.json`:
```json
{
    "version": "2.0.0",
    "tasks": [
        {
            "label": "Find Legacy Imports",
            "type": "shell",
            "command": "grep -r 'from server.queries import' .",
            "presentation": {
                "reveal": "always",
                "panel": "new"
            }
        },
        {
            "label": "Add Migration TODOs",
            "type": "shell",
            "command": "python scripts/add_migration_todos.py",
            "presentation": {
                "reveal": "always",
                "panel": "new"
            }
        }
    ]
}
```

## Step 4: Create Search Patterns

Use these patterns in VSCode's search (Ctrl+Shift+F):

1. Find old imports:
```regex
from\s+server\.queries\s+import\s+([\w,\s]+)
```

2. Find string constants:
```regex
["'](military|financial|humanitarian|refugee_cost_estimation)["']
```

3. Find untyped function parameters:
```regex
def\s+\w+\(((?![:\)])[^)]*)\)
```

## Step 5: Refactoring Steps

1. **Identify Files to Migrate:**
```python
# Run in VSCode terminal
python -c "
import glob
files = glob.glob('**/*.py', recursive=True)
for f in files:
    with open(f) as file:
        if 'from server.queries import' in file.read():
            print(f)
"
```

2. **Add Migration TODOs:**
- Use the migration helper to add TODOs to files
- Use Todo Tree extension to track progress

3. **Replace Imports:**
- Use multi-cursor editing (`Alt+Click`) to update similar lines
- Update one import pattern at a time

4. **Add Type Hints:**
- Use Python Type Hint extension suggestions
- Add return type hints to functions

5. **Update String Constants to Enums:**
- Replace hardcoded strings with enum references
- Use find/replace with regex

## Example Regex Patterns

1. Find old-style column imports:
```regex
from server\.queries import .*?_COLUMNS
```

2. Find dictionary definitions with string keys:
```regex
{\s*["'](military|financial|humanitarian|refugee_cost_estimation)["']\s*:
```

3. Find untyped function parameters:
```regex
def\s+(\w+)\s*\(([^)]*)\)(?!\s*->\s*\w+):
```

## VSCode Shortcuts for Refactoring

- `F2`: Rename symbol
- `Ctrl+.`: Quick fix suggestions
- `Alt+Enter`: Show code actions
- `Shift+Alt+F`: Format document
- `Ctrl+Space`: Trigger suggestions
- `Ctrl+Shift+Space`: Trigger parameter hints

