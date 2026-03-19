"""Local filesystem storage adapter."""

import shutil
from pathlib import Path

from storage.adapter import StorageAdapter


class LocalAdapter(StorageAdapter):
    """Store files on the local filesystem."""

    def __init__(self, config: dict):
        self.output_dir = Path(config.get("output_dir", "./questionnaires/completed"))
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def upload(self, local_path: str, remote_name: str) -> str:
        dest = self.output_dir / remote_name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(local_path, dest)
        return str(dest.resolve())

    def download(self, remote_name: str, local_path: str):
        src = self.output_dir / remote_name
        shutil.copy2(src, local_path)

    def list_files(self, prefix: str = "") -> list:
        files = []
        for f in self.output_dir.rglob("*"):
            if f.is_file():
                rel = str(f.relative_to(self.output_dir))
                if rel.startswith(prefix):
                    files.append(rel)
        return sorted(files)

    def get_share_link(self, remote_name: str) -> str:
        return str((self.output_dir / remote_name).resolve())

    def test_connection(self) -> bool:
        return self.output_dir.exists() and self.output_dir.is_dir()
