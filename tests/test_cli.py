import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from folder_organizer.cli import (  # noqa: E402
    CATEGORIES,
    is_inside_category_folder,
    pick_category,
    unique_destination,
)


class FolderOrganizerHelperTests(unittest.TestCase):
    def test_pick_category_known_extension(self):
        self.assertEqual(pick_category(".py", CATEGORIES), "Code")

    def test_pick_category_unknown_extension(self):
        self.assertEqual(pick_category(".unknown", CATEGORIES), "Other")

    def test_unique_destination_adds_suffix(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "file.txt"
            path.write_text("x", encoding="utf-8")
            new_path = unique_destination(path)
            self.assertEqual(new_path.name, "file (2).txt")

    def test_is_inside_category_folder_true_for_top_level_category(self):
        root = Path("/tmp/example")
        item = root / "Docs" / "notes.txt"
        self.assertTrue(is_inside_category_folder(item, root, {"Docs", "Other"}))

    def test_is_inside_category_folder_false_for_non_category_prefix(self):
        root = Path("/tmp/example")
        item = root / "projects" / "Docs" / "notes.txt"
        self.assertFalse(is_inside_category_folder(item, root, {"Docs", "Other"}))


if __name__ == "__main__":
    unittest.main()
