from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parent.parent


class InstallerTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="skills tooling ")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.agents = self.root / "agents"
        self.claude = self.root / "claude"

    def install(self, *arguments):
        environment = os.environ.copy()
        environment.update(
            AGENTS_SKILLS_DIR=str(self.agents),
            CLAUDE_SKILLS_DIR=str(self.claude),
        )
        return subprocess.run(
            [str(ROOT / "scripts/install"), *arguments],
            cwd=ROOT,
            env=environment,
            capture_output=True,
            text=True,
        )

    def assert_links(self, directory, names):
        self.assertEqual({path.name for path in directory.iterdir()}, names)
        for name in names:
            link = directory / name
            self.assertTrue(link.is_symlink(), str(link))
            self.assertEqual(link.resolve(), ROOT / "skills" / name)

    def test_copied_dependency_blocks_all_writes(self):
        copied = self.agents / "grill-me"
        copied.mkdir(parents=True)
        (copied / "SKILL.md").write_text("Existing user copy\n")

        result = self.install("deliver")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Refusing to replace existing path", result.stderr)
        self.assertEqual(list(self.agents.iterdir()), [copied])
        self.assertEqual((copied / "SKILL.md").read_text(), "Existing user copy\n")
        self.assertFalse(self.claude.exists())

    def test_conflict_in_second_harness_blocks_first_harness(self):
        self.claude.mkdir()
        existing = self.claude / "bro"
        existing.write_text("Keep this file\n")

        result = self.install("bro")

        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.agents.exists())
        self.assertEqual(existing.read_text(), "Keep this file\n")

    def test_unrelated_and_dangling_links_are_preserved(self):
        self.claude.mkdir()
        for name in ("bro", "grill-me"):
            destination = self.root / ("other-" + name)
            if name == "bro":
                destination.mkdir()
            (self.claude / name).symlink_to(destination)

        result = self.install("bro", "grill-me")

        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.agents.exists())
        self.assertEqual(result.stderr.count("Refusing to replace link"), 2)
        for name in ("bro", "grill-me"):
            self.assertEqual(
                (self.claude / name).readlink(), self.root / ("other-" + name)
            )

    def test_unknown_skill_blocks_preceding_valid_skill(self):
        result = self.install("bro", "missing-skill")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Unknown or invalid skill: missing-skill", result.stderr)
        self.assertFalse(self.agents.exists())
        self.assertFalse(self.claude.exists())

    def test_blocked_destination_ancestor_prevents_all_writes(self):
        blocked = self.root / "blocked"
        blocked.write_text("Keep this file\n")
        self.claude = blocked / "nested" / "skills"

        result = self.install("bro")

        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.agents.exists())
        self.assertEqual(blocked.read_text(), "Keep this file\n")

    def test_install_all_is_repeatable(self):
        expected = {path.name for path in (ROOT / "skills").iterdir() if path.is_dir()}

        for _ in range(2):
            result = self.install()
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assert_links(self.agents, expected)
            self.assert_links(self.claude, expected)

    def test_delivery_dependencies_are_installed_for_selected_harness(self):
        result = self.install("--harness", "codex", "deliver")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assert_links(
            self.agents,
            {"deliver", "grill-me", "research", "plan", "implement", "design-review",
             "blast-radius", "bro", "adr"},
        )
        self.assertFalse(self.claude.exists())

    def test_project_plan_installs_adr_only_in_selected_harness(self):
        for harness in ("codex", "pi", "claude"):
            with self.subTest(harness=harness):
                self.agents = self.root / harness / "agents"
                self.claude = self.root / harness / "claude"

                result = self.install("--harness", harness, "project-plan")

                self.assertEqual(result.returncode, 0, result.stderr)
                if harness == "claude":
                    installed, unused = self.claude, self.agents
                else:
                    installed, unused = self.agents, self.claude
                self.assert_links(installed, {"project-plan", "adr"})
                self.assertFalse(unused.exists())

    def test_standalone_interview_has_no_automatic_adr_dependency(self):
        result = self.install("--harness", "claude", "grill-me")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assert_links(self.claude, {"grill-me"})
        self.assertFalse(self.agents.exists())


class ValidatorTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="skills validator ")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.script = self.root / "scripts" / "validate"
        self.script.parent.mkdir()
        shutil.copyfile(ROOT / "scripts/validate", self.script)
        self.skill = self.root / "skills" / "fixture"
        self.skill.mkdir(parents=True)

    def validate(self, metadata):
        (self.skill / "SKILL.md").write_text(
            "---\n" + metadata + "\n---\nSkill instructions.\n"
        )
        return subprocess.run(
            [sys.executable, str(self.script)],
            cwd=self.root,
            capture_output=True,
            text=True,
        )

    def test_rejects_malformed_yaml_and_empty_descriptions(self):
        cases = {
            "malformed YAML": "description: Review changes: check behavior",
            "empty block": "description: |",
            "whitespace": 'description: "   "',
            "missing": "",
        }
        for label, description in cases.items():
            with self.subTest(label=label):
                result = self.validate("name: fixture\n" + description)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("fixture:", result.stderr)
                self.assertNotIn("Traceback", result.stderr)

    def test_requires_string_fields(self):
        for field in ("name", "description"):
            for value in ("42", "true", "null", "[value]", "{key: value}"):
                with self.subTest(field=field, value=value):
                    metadata = {"name": "fixture", "description": "Review changes"}
                    metadata[field] = value
                    result = self.validate(
                        "\n".join(f"{key}: {value}" for key, value in metadata.items())
                    )
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn(f"{field} must be a string", result.stderr)
                    self.assertNotIn("Traceback", result.stderr)

    def test_requires_a_mapping(self):
        for metadata in ("", "plain text", "- name: fixture\n- description: Review changes"):
            with self.subTest(metadata=metadata):
                result = self.validate(metadata)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("frontmatter must be a YAML mapping", result.stderr)

    def test_accepts_quoted_and_multiline_descriptions(self):
        for description in (
            '"Review changes: check behavior"',
            "|\n  Review changes.\n  Check behavior.",
            ">-\n  Review changes\n  and check behavior.",
        ):
            with self.subTest(description=description):
                result = self.validate(
                    "name: fixture # YAML comments are allowed\n"
                    f"description: {description}\n"
                    "metadata:\n  category: review"
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn("OK: fixture", result.stdout)


if __name__ == "__main__":
    unittest.main()
