"""Safety checks for the synthetic public demo entry point."""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DEMO_SCRIPT = REPO_ROOT / "examples" / "demo.py"


class DemoSafetyTests(unittest.TestCase):
    def test_demo_refuses_non_empty_output_directory(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "existing-output"
            output_dir.mkdir()
            marker = output_dir / "keep.txt"
            marker.write_text("preserve this file", encoding="utf-8")

            result = subprocess.run(
                [sys.executable, str(DEMO_SCRIPT), "--output-dir", str(output_dir)],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(marker.read_text(encoding="utf-8"), "preserve this file")
            self.assertEqual(list(output_dir.iterdir()), [marker])


if __name__ == "__main__":
    unittest.main()
