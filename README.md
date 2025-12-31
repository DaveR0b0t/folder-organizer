# folder-organizer

A safe, configurable file organizer CLI with **dry-run by default**, **undo support**, and **JSON-based rules**.

This tool helps you organize folders (Downloads, Desktop, project directories, etc.) by file type without risking accidental data loss.

---

## ✨ Features

- ✅ **Dry run by default** (nothing moves unless you say so)
- 🔁 **Undo support** via log files
- 📁 **Recursive mode** (optional)
- ⚙️ **Custom rules** via JSON config files
- 🧪 Safe handling of name collisions
- 📦 Installable as a real CLI (`organize`)

---

## 🚀 Installation

### Option 1: Install with pipx (recommended)
This installs the CLI globally but safely in its own environment.

```bash
pipx install git+https://github.com/DaveR0b0t/folder-organizer.git
```

### Option 2: Devolpment install(editable):

```
git clone https://github.com/DaveR0b0t/folder-organizer.git
cd folder-organizer

python -m venv .venv
source .venv/bin/activate

pip install -e .
```

🧠 Basic Usage
Dry run (preview only)

```
organize `/Downloads
```
Apply changes:
```
organize ~/Downloads --apply
```
Recursive organize:
```
organize ~/Downloads --recursive
```
🔁 Undo a Run

When you apply changes, a log file is created:
```
organize_log.txt
```
Preview undo:
```
organize --undow ~/Downloads/organize_log.txt
```
Undo for real:
```
organize --undo ~/Downloads/organize_log.txt --apply
```
Undo operations are performed in reverse order and avoid overwriting files.

⚙️ Custom Rules (JSON Config)

You can define your own categories and file extensions using a JSON file.

Example:
```
{
  "Images": [".png", ".jpg", ".jpeg"],
  "Docs": [".pdf", ".txt", ".md"],
  "Code": [".py", ".js", ".ts"]
}
```
Rune with:
```
organize ~/Downloads --config rules.json
```
If a file doesn't match any category, it goes into:
```
Other/<extension>/
```
🛡️ Safety Notes

-The tool never moves files unless --apply is used

-Dry run is always the default

-Undo logs are written only when applying changes

-Existing files are never overwritten (suffixes are added automatically)


📌 Recommended Workflow

1) Run a dry run:
```
organize TARGET_FOLDER
```
2) Review the output
3) Apply changes:
```
organize TARGET_FOLDER --apply
```
4) If needed, undo using the generated log (The log gets placed in Docs during organization)
------------------------

🧩 Python Version

Python 3.10+ required


📄 License

MIT License — see the LICENSE file for details.


👤 Author

DaveR0b0t
Built as a learning project and evolved into a reusable CLI tool.
