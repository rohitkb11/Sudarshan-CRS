import tempfile
import unittest
from pathlib import Path

from orchestrator.pipeline.patch_memory import PatchMemory


class PatchMemorySQLiteTests(unittest.TestCase):
    def test_sqlite_backend_initialization_and_crud(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
            db_path = Path(temp_dir) / "patch_memory.db"
            mem = PatchMemory(db_path)
            self.assertTrue(mem.is_sqlite)

            mem.record(
                bug_class="CWE-120",
                root_cause="Unchecked buffer copy",
                fix_pattern="Add length bounds check",
                crash_signature="ERROR: AddressSanitizer: stack-buffer-overflow",
                target="example-target",
            )

            entries = mem.list_all()
            self.assertEqual(len(entries), 1)
            self.assertEqual(entries[0]["bug_class"], "CWE-120")
            self.assertEqual(entries[0]["target"], "example-target")

            # Lookup by bug class
            found = mem.lookup("CWE-120")
            self.assertIsNotNone(found)
            self.assertEqual(found["fix_pattern"], "Add length bounds check")

            # Statistics check
            stats = mem.get_stats()
            self.assertEqual(stats["total_verified_fixes"], 1)
            self.assertEqual(stats["storage_backend"], "sqlite")
            self.assertEqual(stats["by_bug_class"]["CWE-120"], 1)


if __name__ == "__main__":
    unittest.main()
