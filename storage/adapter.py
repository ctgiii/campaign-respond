"""Storage adapter abstraction for Campaign Respond."""

import json
from abc import ABC, abstractmethod
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


class StorageAdapter(ABC):
    """Base interface for storage providers."""

    @abstractmethod
    def upload(self, local_path: str, remote_name: str) -> str:
        """Upload a file. Returns URL or path."""
        pass

    @abstractmethod
    def download(self, remote_name: str, local_path: str):
        """Download a file."""
        pass

    @abstractmethod
    def list_files(self, prefix: str = "") -> list:
        """List files with optional prefix filter."""
        pass

    @abstractmethod
    def get_share_link(self, remote_name: str) -> str:
        """Get a shareable link for a file."""
        pass

    @abstractmethod
    def test_connection(self) -> bool:
        """Test that the storage connection works."""
        pass


def get_storage_adapter() -> StorageAdapter | None:
    """Get the configured storage adapter.

    Returns:
        StorageAdapter instance, or None if no storage configured
    """
    config_path = BASE_DIR / "config" / "storage.json"
    if not config_path.exists():
        return None

    with open(config_path) as f:
        config = json.load(f)

    provider = config.get("provider", "local")

    if provider == "local":
        from storage.local import LocalAdapter
        return LocalAdapter(config.get("local", {}))

    elif provider == "google_drive":
        from storage.google_drive import GoogleDriveAdapter
        return GoogleDriveAdapter(config.get("google_drive", {}))

    elif provider == "onedrive":
        from storage.onedrive import OneDriveAdapter
        return OneDriveAdapter(config.get("onedrive", {}))

    elif provider == "proton_drive":
        from storage.local import LocalAdapter
        # Proton Drive is just a local mount
        mount = config.get("proton_drive", {}).get("mount_path", "")
        return LocalAdapter({"output_dir": mount})

    else:
        print(f"Unknown storage provider: {provider}")
        return None
