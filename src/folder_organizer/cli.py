import argparse
import json
import shutil
from pathlib import Path



CATEGORIES = {
    "Images": {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".tiff"},
    "Videos": {".mp4", ".mkv", ".mov", ".avi", ".webm", ".m4v"},
    "Audio": {".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a"},
    "Docs": {".pdf", ".txt", ".doc", ".docx", ".md", ".rtf", ".odt"},
    "Sheets": {".csv", ".xls", ".xlsx", ".ods"},
    "Slides": {".ppt", ".pptx", ".odp"},
    "Archives": {".zip", ".rar", ".7z", ".tar", ".gz"},
    "Code": {".py", ".js", ".ts", ".html", ".css", ".json", ".xml", ".yml", ".yaml"},
}


def load_categories_from_json(config_path: Path) -> dict[str, set[str]]:
    """
    Load Categories from a JSON file.

    Expected JSON format:
    {
      "Images": [".png", ".jpg"],
      "Docs": [".pdf", ".txt"]
    }

    Returns:
      dict where each category maps to a set of lowercase extensions.

    :param config_path:
    :return:
    """

    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    # Read JSON text and parse into Python objects (dict/list)
    data = json.loads(config_path.read_text(encoding="utf-8"))


    if not isinstance(data, dict):
        raise ValueError("Config JSON must be an object/dictionary at the top level.")

    categories: dict[str, set[str]] = {}
    for category, exts in data.items():
        if not isinstance(category, str) or not category.strip():
            raise ValueError("Category names in config must be non-empty strings.")

        if not isinstance(exts, list):
            raise ValueError(f"Extensions for '{category}' must be a list.")

        clean_exts = set()
        for ext in exts:
            if not isinstance(ext, str) or not ext.strip():
                raise ValueError(f"Invalid extension value in '{category}': {ext!r}")
            e = ext.strip().lower()
            # Normalize: ensure it starts with a dot
            if not e.startswith("."):
                e = "." + e
            clean_exts.add(e)

        categories[str(category).strip()] = clean_exts

    return categories


def pick_category(ext: str, categories: dict[str, set[str]]) -> str:
    """
    :param ext:
    :param categories:
    :return:
    """

    ext = ext.lower()
    for category, exts in categories.items():
        if ext in exts:
            return category
    return "Other"


def unique_destination(dest: Path) -> Path:
    """If dest exists, add ' (2)', ' (3)' etc. before the suffix."""
    if not dest.exists():
        return dest

    stem, suffix, parent = dest.stem, dest.suffix, dest.parent
    n = 2
    while True:
        candidate = parent / f"{stem} ({n}){suffix}"
        if not candidate.exists():
            return candidate
        n += 1


def is_inside_category_folder(item: Path, root: Path, category_names: set[str]) -> bool:
    """True if item is anywhere under Images/, Docs/, Other/, etc. inside root."""
    try:
        rel_parts = item.relative_to(root).parts
    except ValueError:
        return False  # item not under root for some reason
    return any(part in category_names for part in rel_parts)


def organize(folder: Path, dry_run: bool, recursive: bool,
             categories: dict[str, set[str]],
             log_file: Path | None = None):

    category_names = set(categories.keys()) | {"Other"}

    if not folder.exists() or not folder.is_dir():
        print("That folder does not exist or is not a directory.")
        return

    moved = 0
    this_script = Path(__file__).resolve()
    iterator = folder.rglob("*") if recursive else folder.iterdir()
    log_handle = None
    if (not dry_run) and log_file is not None:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        log_handle = open(log_file, "w", encoding="utf-8")

    for item in iterator:
        if item.is_dir():
            continue

        if item.name.startswith("."):
            continue

        # Don't move the running script itself
        if item.resolve() == this_script:
            continue

        # Skip anything already under category folders (even nested)
        if is_inside_category_folder(item, folder, category_names):
            continue

        category = pick_category(item.suffix, categories)

        if category == "Other":
            ext = item.suffix.lower() if item.suffix else "NoExtension"
            target_dir = folder / "Other" / ext
        else:
            target_dir = folder / category

        target_path = unique_destination(target_dir / item.name)

        if dry_run:
            print(f"[DRY RUN] Move: {item.relative_to(folder)} -> {target_dir.relative_to(folder)}/{target_path.name}")
        else:
            target_dir.mkdir(parents=True, exist_ok=True)
            shutil.move(str(item), str(target_path))
            print(f"Moved: {item.relative_to(folder)} -> {target_dir.relative_to(folder)}/{target_path.name}")
            moved += 1

            if log_handle:
                log_handle.write(f"{item.resolve()}\t{target_path.resolve()}\n")
                log_handle.flush()


    if dry_run:
        print("\nDone (dry run). No files were moved.")
    else:
        print(f"\nDone. Moved {moved} file(s).")

    if log_handle:
        log_handle.close()
        print(f"Log saved to: {log_file}")


def undo_moves(log_file: Path, dry_run: bool = True):
    """
    Read a log of moves and reverse them.
    Log format (tab-seperated): FROM<TAB>TO
    We undo in reverse order so nested moves don't break.
    """
    if not log_file.exists():
        print(f"Log file not found: {log_file}")
        return

    lines = log_file.read_text(encoding="utf-8").splitlines()
    moves = []
    for line in lines:
        if not line.strip():
            continue
        try:
            src, dst = line.split("\t", 1) # src=FROM, dst=TO
        except ValueError:
            print(f"Skipping invalid log line: {line}")
            continue
        moves.append((Path(src), Path(dst)))

    if not moves:
        print("No moves found in log.")
        return

    undone = 0
    # Reverse order matters
    for src, dst in reversed(moves):
        # To undo: move dst back to src
        if not dst.exists():
            print(f"Missing (can't undo) {dst}")
            continue

        src_parent = src.parent
        if dry_run:
            print(f"[DRY RUN] Undo: {dst} -> {src}")
        else:
            src_parent.mkdir(parents=True, exist_ok=True)

            # Avoid overwriting if something now exists at src
            final_src = unique_destination(src)
            shutil.move(str(dst), str(final_src))
            print(f"Undone: {dst.name} -> {final_src}")
            undone += 1

    if dry_run:
        print("\nDone (dry run). No files were moved back.")
    else:
        print(f"\nDone. Undid {undone} move(s).")



def parse_args():
    """
    Create and configure the command-line interface.

    argparse automatically:
    - parses arguments from sys.argv
    - validates them
    - generates --help output
    """
    # Create the main argument parser
    parser = argparse.ArgumentParser(
        description="Organize files in a folder by type"
    )

    # Positional argument:
    # This is the folder path the user wants to organize.
    # - nargs="?" makes it optional
    # - default="." means: use the current directory if not provided
    parser.add_argument(
        "folder",
        nargs="?",
        default=".",
        help="Folder to organize (default: current folder)"
    )
    # Optional config file for custom categories/extensions

    parser.add_argument(
        "--config",
        metavar="JSONFILE",
        help="Path to a JSON config file that defines categories and extensions"
    )

    # Undo log
    # So user can undo the move
    parser.add_argument(
        "--undo",
        metavar="LOGFILE",
        help="Undo a previous run using given log file (no organizing will happen)"
    )

    # Flag argument:
    # --apply is False by default
    # If user includes --apply, it becomes True
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Actually move files (default is dry run)"
    )

    # Another flag argument:
    # When --recursive is present, organize subfolders too
    # Without it, only the top-level folder is processed
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Organize subfolders recursively"
    )
    
    # Version number
    parser.add_argument("--version", action="version", version="folder-organizer 0.1.0")


    # Parse the arguments and return them as a namespace object
    # Example: args.folder, args,apply, args.recursive
    return parser.parse_args()


def main():
    # Read and parse all CLI arguments
    args = parse_args()

    # Safety-first design:
    # - default behavior is dry run
    # - user must explicitly pass --apply to move files
    dry_run = not args.apply

    # Start with built-in defaults
    active_categories = CATEGORIES

    # If user provided --config, load categories from that JSON file
    if args.config:
        config_path = Path(args.config).expanduser().resolve()
        try:
            active_categories = load_categories_from_json(config_path)
            print("Using config:", config_path)
        except (FileNotFoundError, ValueError, json.JSONDecodeError) as e:
            print("Config error:", e)
            return


    # If --undo is used, we ONLY undo (no organizing)
    if args.undo:
        log_file = Path(args.undo).expanduser().resolve()
        print("=== Undo Mode ===")
        print("Log file:", log_file)
        print("Mode:", "DRY RUN" if dry_run else "APPLY")
        print()
        undo_moves(log_file, dry_run=dry_run)
        return

    # convert the folder argument into an absolute Path object
    # Path makes filesystem work safer and cleaner
    folder = Path(args.folder).expanduser().resolve()

    # Whether we should scan subfolders
    recursive = args.recursive

    # Default log file name (timestamp-free simple version)
    log_file = folder / "organize_log.txt"

    # For now, just show what the script "would" do
    print("=== Folder Organizer ===")
    print("Folder:", folder)
    print("Mode:", "DRY RUN" if dry_run else "APPLY")
    print("Recursive:", recursive)
    if not dry_run:
        print("Log:", log_file)
    print()

    organize(
        folder=folder,
        dry_run=dry_run,
        recursive=recursive,
        categories=active_categories,
        log_file=log_file
    )

# This block ensures main() only runs when:
# - the file is executed directly (python organize_cli.py)
# - NOT when it is imported by another script

if __name__ == "__main__":
    main()

