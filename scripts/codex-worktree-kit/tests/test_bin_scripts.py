import os
import subprocess
import tempfile
import unittest
from pathlib import Path


class BinScriptTests(unittest.TestCase):
    def test_validate_config_wrapper_uses_project_venv_python(self) -> None:
        project_root = Path(__file__).resolve().parent.parent
        fake_bin = Path(tempfile.mkdtemp())
        fake_python = fake_bin / "python3"
        fake_python.write_text("#!/usr/bin/env bash\nexit 99\n", encoding="utf-8")
        fake_python.chmod(0o755)

        env = os.environ.copy()
        env["PATH"] = f"{fake_bin}:{env['PATH']}"

        completed = subprocess.run(
            [
                str(project_root / "bin" / "codex-worktree-validate-config"),
                "--config",
                str(project_root / "examples" / "backend.worktree.toml"),
            ],
            cwd=project_root,
            env=env,
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("valid:", completed.stdout)


if __name__ == "__main__":
    unittest.main()
