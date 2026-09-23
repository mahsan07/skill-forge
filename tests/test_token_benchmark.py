import sys
import unittest

from skill_forge.token_benchmark import estimate_tokens, run_benchmark


class TokenBenchmarkTest(unittest.TestCase):
    def test_identity_preserves_facts(self):
        fixtures = [{
            "id": "handoff",
            "text": "Keep API stable. Run tests. Do not delete data.",
            "must_contain": ["API", "Run tests", "Do not delete data"],
        }]
        report = run_benchmark(fixtures, {"control": {"kind": "identity"}})
        run = report["runs"][0]
        self.assertEqual(run["status"], "pass")
        self.assertEqual(run["critical_fact_retention_pct"], 100.0)
        self.assertEqual(run["estimated_token_reduction_pct"], 0.0)

    def test_stdin_adapter_measures_compression(self):
        fixtures = [{
            "id": "noise",
            "text": "noise noise KEEP noise noise",
            "must_contain": ["KEEP"],
        }]
        adapters = {
            "compact": {
                "kind": "stdin_command",
                "command": [
                    sys.executable,
                    "-c",
                    "import sys; print(sys.stdin.read().replace('noise ', ''), end='')",
                ],
            }
        }
        report = run_benchmark(fixtures, adapters)
        run = report["runs"][0]
        self.assertEqual(run["status"], "pass")
        self.assertGreater(run["estimated_token_reduction_pct"], 0)
        self.assertTrue(run["non_expanding"])

    def test_missing_fact_fails_even_when_smaller(self):
        fixtures = [{
            "id": "lossy",
            "text": "KEEP MUST_NOT_LOSE extra words",
            "must_contain": ["KEEP", "MUST_NOT_LOSE"],
        }]
        adapters = {
            "bad": {
                "kind": "stdin_command",
                "command": [sys.executable, "-c", "print('KEEP')"],
            }
        }
        report = run_benchmark(fixtures, adapters)
        run = report["runs"][0]
        self.assertEqual(run["status"], "fail")
        self.assertEqual(run["missing_critical_facts"], ["MUST_NOT_LOSE"])

    def test_file_rewrite_adapter_reads_rewritten_file(self):
        fixtures = [{
            "id": "memory",
            "text": "KEEP filler filler",
            "must_contain": ["KEEP"],
            "suffix": ".md",
        }]
        adapters = {
            "rewrite": {
                "kind": "file_rewrite_command",
                "command": [
                    sys.executable,
                    "-c",
                    "from pathlib import Path; import sys; p=Path(sys.argv[1]); p.write_text(p.read_text().replace(' filler',''), encoding='utf-8')",
                    "{input_file}",
                ],
            }
        }
        report = run_benchmark(fixtures, adapters)
        self.assertEqual(report["runs"][0]["status"], "pass")
        self.assertGreater(report["runs"][0]["estimated_token_reduction_pct"], 0)

    def test_estimate_tokens_empty(self):
        self.assertEqual(estimate_tokens(""), 0)


if __name__ == "__main__":
    unittest.main()
