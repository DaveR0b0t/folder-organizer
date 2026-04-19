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
    Load categories from a JSON file.

    Expected JSON format:
    {
      "Images": [".png", ".jpg"],
      "Docs": [".pdf", ".txt"]
    }
    """
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

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
            if not e.startswith("."):
                e = "." + e
            clean_exts.add(e)

        categories[str(category).strip()] = clean_exts

    return categories



def pick_category(ext: str, categories: dict[str, set[str]]) -> str:
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
    """True if item is already under a top-level category folder inside root."""
    try:
        rel_parts = item.relative_to(root).parts
    except ValueError:
        return False

    if not rel_parts:
        return False

    return rel_parts[0] in category_names



def organize(
    folder: Path,
    dry_run: bool,
    recursive: bool,
    categories: dict[str, set[str]],
    log_file: Path | None = None,
):
    category_names = set(categories.keys()) | {"Other"}

    if not folder.exists() or not folder.is_dir():
        print("That folder does not exist or is not a directory.")
        return

    moved = 0
    this_script = Path(__file__).resolve()
    iterator = folder.rglob("*") if recursive else folder.iterdir()
    log_handle = None
    log_file_resolved = log_file.resolve() if log_file is not None else None

    if (not dry_run) and log_file is not None:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        log_handle = open(log_file, "w", encoding="utf-8")

    for item in iterator:
        if item.is_dir():
            continue

        if item.name.startswith("."):
            continue

        if item.resolve() == this_script:
            continue

        if log_file_resolved is not None and item.resolve() == log_file_resolved:
            continue

        if is_inside_category_folder(item, folder, category_names):
            continue

        category = pick_category(item.suffix, categories)

        if category == "Other":
            ext = item.suffix.lower().lstrip(".") if item.suffix else "no_extension"
            target_dir = folder / "Other" / ext
        else:
            target_dir = folder / category

        target_path = unique_destination(target_dir / item.name)
        destination_display = f"{target_dir.relative_to(folder)}/{target_path.name}"

        if dry_run:
            print(f"[DRY RUN] Move: {item.relative_to(folder)} -> {destination_display}")
        else:
            target_dir.mkdir(parents=True, exist_ok=True)
            shutil.move(str(item), str(target_path))
            print(f"Moved: {item.relative_to(folder)} -> {destination_display}")
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
    Log format (tab-separated): FROM<TAB>TO
    We undo in reverse order so nested moves do not break.
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
            src, dst = line.split("\t", 1)
        except ValueError:
            print(f"Skipping invalid log line: {line}")
            continue
        moves.append((Path(src), Path(dst)))

    if not moves:
        print("No moves found in log.")
        return

    undone = 0
    for src, dst in reversed(moves):
        if not dst.exists():
            print(f"Missing (can't undo) {dst}")
            continue

        src_parent = src.parent
        if dry_run:
            print(f"[DRY RUN] Undo: {dst} -> {src}")
        else:
            src_parent.mkdir(parents=True, exist_ok=True)
            final_src = unique_destination(src)
            shutil.move(str(dst), str(final_src))
            print(f"Undone: {dst.name} -> {final_src}")
            undone += 1

    if dry_run:
        print("\nDone (dry run). No files were moved back.")
    else:
        print(f"\nDone. Undid {undone} move(s).")



def parse_args():
    parser = argparse.ArgumentParser(
        description="Organize files in a folder by type"
    )

    parser.add_argument(
        "folder",
        nargs="?",
        default=".",
        help="Folder to organize (default: current folder)"
    )

    parser.add_argument(
        "--config",
        metavar="JSONFILE",
        help="Path to a JSON config file that defines categories and extensions"
    )

    parser.add_argument(
        "--undo",
        metavar="LOGFILE",
        help="Undo a previous run using given log file (no organizing will happen)"
    )

    parser.add_argument(
        "--apply",
        action="store_true",
        help="Actually move files (default is dry run)"
    )

    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Organize subfolders recursively"
    )

    parser.add_argument("--version", action="version", version="folder-organizer 0.1.0")

    return parser.parse_args()



def main():
    args = parse_args()
    dry_run = not args.apply
    active_categories = CATEGORIES

    if args.config:
        config_path = Path(args.config).expanduser().resolve()
        try:
            active_categories = load_categories_from_json(config_path)
            print("Using config:", config_path)
        except (FileNotFoundError, ValueError, json.JSONDecodeError) as e:
            print("Config error:", e)
            return

    if args.undo:
        log_file = Path(args.undo).expanduser().resolve()
        print("=== Undo Mode ===")
        print("Log file:", log_file)
        print("Mode:", "DRY RUN" if dry_run else "APPLY")
        print()
        undo_moves(log_file, dry_run=dry_run)
        return

    folder = Path(args.folder).expanduser().resolve()
    recursive = args.recursive
    log_file = folder / "organize_log.txt"

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
        log_file=log_file,
    )


if __name__ == "__main__":
    main()
