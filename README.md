# folder-organizer

[![Tests](https://github.com/DaveR0b0t/folder-organizer/actions/workflows/tests.yml/badge.svg)](https://github.com/DaveR0b0t/folder-organizer/actions/workflows/tests.yml)

folder-organizer is a safe and configurable file organizer CLI with dry run mode by default, undo support, and JSON-based rules.

It helps you organize folders such as Downloads, Desktop, or project directories by file type without moving anything until you explicitly apply the changes.

## Features

- Dry run by default
- Undo support through log files
- Optional recursive mode
- Custom rules through JSON config files
- Safe handling of name collisions
- Installable CLI command: `organize`

## Installation

### Option 1: Install with pipx

```bash
pipx install git+https://github.com/DaveR0b0t/folder-organizer.git
```

### Option 2: Development install

```bash
git clone https://github.com/DaveR0b0t/folder-organizer.git
cd folder-organizer

python -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Basic Usage

### Dry run

```bash
organize ~/Downloads
```

### Apply changes

```bash
organize ~/Downloads --apply
```

### Recursive organization

```bash
organize ~/Downloads --recursive
```

## Undo a Run

When you apply changes, a log file named `organize_log.txt` is created in the target folder.

### Preview undo

```bash
organize --undo ~/Downloads/organize_log.txt
```

### Undo for real

```bash
organize --undo ~/Downloads/organize_log.txt --apply
```

Undo operations run in reverse order and avoid overwriting files.

## Custom Rules

You can define your own categories and file extensions in a JSON file.

Example:

```json
{
  "Images": [".png", ".jpg", ".jpeg"],
  "Docs": [".pdf", ".txt", ".md"],
  "Code": [".py", ".js", ".ts"]
}
```

Run with a custom config:

```bash
organize ~/Downloads --config rules.json
```

If a file does not match any category, it is placed into:

```text
Other/<extension>/
```

Files without an extension are placed into:

```text
Other/no_extension/
```

## Safety Notes

- Files are not moved unless `--apply` is used
- Dry run is the default behavior
- Undo logs are only written during apply mode
- Existing files are never overwritten, numbered suffixes are added instead

## Recommended Workflow

1. Run a dry run
2. Review the output
3. Apply changes if the result looks correct
4. Use the generated log file to undo changes if needed

## Requirements

- Python 3.10+

## Running Tests

```bash
python -m unittest discover -s tests
```

## License

MIT License. See the LICENSE file for details.

## Author

DaveR0b0t

Built as a learning project and expanded into a reusable CLI tool.
