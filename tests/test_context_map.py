import tempfile
import unittest
from pathlib import Path

from orchestrator.pipeline.context_map import (
    build_context_map,
    context_slice,
    get_function_slice,
)


class ContextMapTests(unittest.TestCase):
    def test_build_context_map_indexes_functions_and_calls(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            src_dir = Path(temp_dir) / "src"
            src_dir.mkdir()
            c_file = src_dir / "app.c"
            c_file.write_text(
                "int helper(int x) {\n    return x + 1;\n}\n\nint main_app() {\n    helper(42);\n    return 0;\n}\n",
                encoding="utf-8",
            )

            cmap = build_context_map(Path(temp_dir))
            self.assertIn("helper", cmap)
            self.assertIn("main_app", cmap)
            self.assertEqual(cmap["helper"]["start_line"], 1)
            self.assertIn("helper", cmap["main_app"]["callees"])

    def test_context_slice_returns_surrounding_window(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            src_dir = Path(temp_dir) / "src"
            src_dir.mkdir()
            c_file = src_dir / "app.c"
            c_file.write_text("\n".join(f"line_{i}" for i in range(1, 30)), encoding="utf-8")

            slice_text = context_slice(Path(temp_dir), "src/app.c", "line_15", radius=3)
            self.assertIn("line_15", slice_text)
            self.assertIn("line_12", slice_text)
            self.assertIn("line_18", slice_text)
            self.assertNotIn("line_5", slice_text)


if __name__ == "__main__":
    unittest.main()
