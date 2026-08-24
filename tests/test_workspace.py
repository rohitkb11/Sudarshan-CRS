import tempfile
import unittest
from pathlib import Path

from orchestrator.pipeline.artifacts import write_patch
from orchestrator.pipeline.workspace import create_workspace


class WorkspaceTests(unittest.TestCase):
    def test_workspace_copy_does_not_change_source(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "target"
            source.mkdir()
            (source / "sample.txt").write_text("original", encoding="utf-8")
            workspace = create_workspace(source, root / "runs")
            (workspace / "sample.txt").write_text("patched", encoding="utf-8")
            self.assertEqual((source / "sample.txt").read_text(encoding="utf-8"), "original")

    def test_patch_artifact_is_unified_diff(self):
        with tempfile.TemporaryDirectory() as temporary:
            patch = write_patch("unsafe();\n", "safe();\n", "src/example.c", Path(temporary) / "fix.patch")
            self.assertIsNotNone(patch)
            self.assertIn("-unsafe();", patch.read_text(encoding="utf-8"))
            self.assertIn("+safe();", patch.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
