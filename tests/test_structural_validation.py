import unittest
from orchestrator.pipeline.patch_gen import validate_patch_structure


class StructuralValidationTests(unittest.TestCase):
    def test_rejects_empty_patch(self):
        code = "int test() { return 0; }"
        valid, reason = validate_patch_structure(code, code)
        self.assertFalse(valid)
        self.assertIn("empty", reason)

    def test_rejects_hardcoded_pov_payload(self):
        before = 'int test(char *in) { char b[16]; strcpy(b, in); }'
        after = 'int test(char *in) { if (strcmp(in, "CRASH_PAYLOAD_12345") == 0) return 0; char b[16]; strcpy(b, in); }'
        valid, reason = validate_patch_structure(before, after, pov_bytes=b"CRASH_PAYLOAD_12345")
        self.assertFalse(valid)
        self.assertIn("hardcodes", reason)

    def test_accepts_defensive_bounds_check(self):
        before = 'int test(char *in) { char b[16]; strcpy(b, in); }'
        after = 'int test(char *in) { char b[16]; if (strlen(in) >= sizeof(b)) return 2; strcpy(b, in); }'
        valid, reason = validate_patch_structure(before, after, pov_bytes=b"CRASH_PAYLOAD_12345")
        self.assertTrue(valid)


if __name__ == "__main__":
    unittest.main()
