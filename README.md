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
