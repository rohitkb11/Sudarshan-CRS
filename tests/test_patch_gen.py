import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from orchestrator.config import Settings
from orchestrator.pipeline.llm_patch import LLMPatchResult, llm_generate_patch
from orchestrator.pipeline.patch_gen import (
    RULE_REGISTRY,
    apply_rule_patch,
    generate_patch,
)
from orchestrator.pipeline.patch_memory import PatchMemory


class PatchGenTests(unittest.TestCase):
    def test_strcpy_rule_applies(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            src_dir = Path(temp_dir) / "src"
            src_dir.mkdir()
            c_file = src_dir / "target.c"
            c_file.write_text(
                'int parse(const char *input) {\n    char buffer[16];\n    strcpy(buffer, input);\n    return 0;\n}\n',
                encoding="utf-8",
            )

            outcome = apply_rule_patch(Path(temp_dir))
            self.assertTrue(outcome.applied)
            self.assertEqual(outcome.bug_class, "CWE-120")
            self.assertIn("sizeof(buffer)", c_file.read_text(encoding="utf-8"))

    def test_sprintf_rule_applies(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            src_dir = Path(temp_dir) / "src"
            src_dir.mkdir()
            c_file = src_dir / "target.c"
            c_file.write_text(
                'int parse(const char *input) {\n    char buffer[16];\n    sprintf(buffer, "%s", input);\n    return 0;\n}\n',
                encoding="utf-8",
            )

            outcome = apply_rule_patch(Path(temp_dir))
            self.assertTrue(outcome.applied)
            self.assertIn("snprintf", c_file.read_text(encoding="utf-8"))

    def test_gets_rule_applies(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            src_dir = Path(temp_dir) / "src"
            src_dir.mkdir()
            c_file = src_dir / "target.c"
            c_file.write_text(
                'void read_input() {\n    char buffer[64];\n    gets(buffer);\n}\n',
                encoding="utf-8",
            )

            outcome = apply_rule_patch(Path(temp_dir))
            self.assertTrue(outcome.applied)
            self.assertEqual(outcome.bug_class, "CWE-676")
            self.assertIn("fgets", c_file.read_text(encoding="utf-8"))

    def test_strcat_rule_applies(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            src_dir = Path(temp_dir) / "src"
            src_dir.mkdir()
            c_file = src_dir / "target.c"
            c_file.write_text(
                'void append(const char *input) {\n    char buffer[32] = "pre:";\n    strcat(buffer, input);\n}\n',
                encoding="utf-8",
            )

            outcome = apply_rule_patch(Path(temp_dir))
            self.assertTrue(outcome.applied)
            self.assertIn("strncat", c_file.read_text(encoding="utf-8"))

    def test_patch_memory_lookup_used_on_attempt_2(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir)
            src_dir = target / "src"
            src_dir.mkdir()
            c_file = src_dir / "complex.c"
            c_file.write_text("void complex_func() { custom_copy(); }", encoding="utf-8")

            memory_file = target / "memory.jsonl"
            mem = PatchMemory(memory_file)
            mem.record("CWE-120", "Buffer overrun", "Check boundary before copy")

            with patch("orchestrator.pipeline.patch_gen.llm_generate_patch") as mock_llm:
                mock_llm.return_value = None
                outcome = generate_patch(
                    target,
                    crash_signature="ERROR: AddressSanitizer: global-buffer-overflow",
                    patch_memory=mem,
                    attempt=2,
                )
                self.assertFalse(outcome.applied)
                mock_llm.assert_called_once()
                call_kwargs = mock_llm.call_args[1]
                self.assertEqual(call_kwargs["patch_memory_hint"]["bug_class"], "CWE-120")
                self.assertEqual(call_kwargs["model_tier"], "strong")

    def test_groq_llm_patch_invocation(self):
        mock_settings = Settings(
            groq_api_key="gsk_test_key",
            llm_provider="groq",
            groq_model_fast="llama-3.1-8b-instant",
        )
        mock_groq_mod = MagicMock()
        mock_client = MagicMock()
        mock_groq_mod.Groq.return_value = mock_client
        mock_choice = MagicMock()
        mock_choice.message.content = json.dumps({
            "root_cause": "Buffer overflow in copy",
            "fix_pattern": "Add bounds check",
            "patched_full_file": "int safe() { return 0; }",
        })
        mock_client.chat.completions.create.return_value.choices = [mock_choice]

        with patch("orchestrator.pipeline.llm_patch.settings", mock_settings), \
             patch.dict("sys.modules", {"groq": mock_groq_mod}):

            result = llm_generate_patch(
                source_content="int unsafe() { ... }",
                filename="src/target.c",
                context_slice="unsafe();",
                crash_signature="ERROR: AddressSanitizer: heap-buffer-overflow",
                model_tier="fast",
            )

            self.assertIsNotNone(result)
            self.assertEqual(result.patched_content, "int safe() { return 0; }")
            self.assertEqual(result.root_cause, "Buffer overflow in copy")
            mock_client.chat.completions.create.assert_called_once()
            call_kwargs = mock_client.chat.completions.create.call_args[1]
            self.assertEqual(call_kwargs["model"], "llama-3.1-8b-instant")

    def test_qwen_reasoning_model_with_think_tags(self):
        mock_settings = Settings(
            groq_api_key="gsk_test_key",
            llm_provider="groq",
            groq_model_strong="qwen/qwen3.6-27b",
            groq_temperature=0.6,
            groq_top_p=0.95,
            groq_max_completion_tokens=2048,
            groq_reasoning_effort="default",
        )
        mock_groq_mod = MagicMock()
        mock_client = MagicMock()
        mock_groq_mod.Groq.return_value = mock_client
        mock_choice = MagicMock()
        mock_choice.message.content = (
            "<think>Analyzing stack buffer overflow in parse_message. Unchecked strcpy into 16-byte buffer.</think>\n"
            "```json\n"
            "{\n"
            '  "root_cause": "Unbounded strcpy into 16-byte stack buffer",\n'
            '  "fix_pattern": "Check strlen before copy",\n'
            '  "patched_full_file": "int parse_message(const char *in) { char b[16]; if (strlen(in)>=sizeof(b)) return 2; strcpy(b,in); return 0; }"\n'
            "}\n"
            "```"
        )
        mock_client.chat.completions.create.return_value.choices = [mock_choice]

        with patch("orchestrator.pipeline.llm_patch.settings", mock_settings), \
             patch.dict("sys.modules", {"groq": mock_groq_mod}):

            result = llm_generate_patch(
                source_content="int parse_message(...) { ... }",
                filename="src/parser.c",
                context_slice="strcpy(b, in);",
                crash_signature="ERROR: AddressSanitizer: stack-buffer-overflow",
                model_tier="strong",
            )

            self.assertIsNotNone(result)
            self.assertEqual(result.root_cause, "Unbounded strcpy into 16-byte stack buffer")
            self.assertIn("sizeof(b)", result.patched_content)
            call_kwargs = mock_client.chat.completions.create.call_args[1]
            self.assertEqual(call_kwargs["model"], "qwen/qwen3.6-27b")
            self.assertEqual(call_kwargs["temperature"], 0.6)
            self.assertEqual(call_kwargs["top_p"], 0.95)


if __name__ == "__main__":
    unittest.main()
