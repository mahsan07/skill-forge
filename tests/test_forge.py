import tempfile
import unittest
from pathlib import Path

from skill_forge import create_skill, inspect_skill


class SkillForgeTest(unittest.TestCase):
    def test_create_and_validate_skill(self):
        with tempfile.TemporaryDirectory() as temporary:
            skill = create_skill(
                temporary,
                "summarize-evidence",
                "Summarize supplied evidence into a concise brief. Use when a user asks for an evidence-backed summary.",
                resources=("references",),
            )
            report = inspect_skill(skill)
            self.assertTrue(report["valid"], report)
            self.assertTrue((skill / "agents/openai.yaml").exists())
            self.assertTrue((skill / "references").is_dir())
            self.assertFalse((skill / "README.md").exists())

    def test_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as temporary:
            create_skill(temporary, "safe-skill", "Perform a safe task. Use when safe task execution is requested.")
            with self.assertRaises(FileExistsError):
                create_skill(temporary, "safe-skill", "Perform it again. Use when requested.")

    def test_invalid_options_leave_no_partial_skill(self):
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaisesRegex(ValueError, "unsupported resource"):
                create_skill(temporary, "clean-skill", "Perform a clean workflow. Use when requested.", resources=("unknown",))
            self.assertFalse((Path(temporary) / "clean-skill").exists())

    def test_invalid_frontmatter_and_public_data_are_reported(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "bad-skill"
            root.mkdir()
            (root / "SKILL.md").write_text("---\nname: Bad_Name\ndescription: vague\nowner: me\n---\nTODO\n", encoding="utf-8")
            (root / "notes.txt").write_text("api_key=EXAMPLE_NOT_A_SECRET_1234", encoding="utf-8")
            report = inspect_skill(root)
            self.assertFalse(report["valid"])
            self.assertTrue(report["public_scrub"])
            self.assertLess(report["score"], 100)

    def test_example_package_is_valid(self):
        example = Path(__file__).parents[1] / "examples" / "evidence-first-qa"
        report = inspect_skill(example)
        self.assertTrue(report["valid"], report)


if __name__ == "__main__":
    unittest.main()
