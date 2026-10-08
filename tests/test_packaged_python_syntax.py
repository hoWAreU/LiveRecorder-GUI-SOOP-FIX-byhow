from __future__ import annotations

import os
import tokenize
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKIP_DIRS = {".venv", ".git", ".github", "__pycache__", "downloads", "logs", "backup_config"}


class PackagedPythonSyntaxTests(unittest.TestCase):
    def test_packaged_python_sources_compile(self) -> None:
        sources = list(ROOT.glob("*.py"))
        for source_dir in (ROOT / "recorder-core", ROOT / "webui"):
            for current, directories, filenames in os.walk(source_dir):
                directories[:] = [name for name in directories if name not in SKIP_DIRS]
                sources.extend(Path(current) / name for name in filenames if name.endswith(".py"))

        self.assertTrue(sources)
        for source in sources:
            with self.subTest(path=str(source.relative_to(ROOT))):
                with tokenize.open(source) as handle:
                    compile(handle.read(), str(source), "exec")


if __name__ == "__main__":
    unittest.main()
