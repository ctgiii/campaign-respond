"""OneDrive storage adapter."""

import json
import os
from pathlib import Path

from storage.adapter import StorageAdapter, BASE_DIR


class OneDriveAdapter(StorageAdapter):
    """Upload/download files to OneDrive."""

    def __init__(self, config: dict):
        self.folder_path = config.get("folder_path", "/Campaign Respond")
        self.credentials_path = Path(
            config.get("credentials_path",
                       str(BASE_DIR / "storage/credentials/onedrive-token.json"))
        )
        self._token = None

    @property
    def token(self):
        if self._token is None:
            self._token = self._authenticate()
        return self._token

    def _authenticate(self) -> str:
        """Authenticate with Microsoft Graph API via MSAL."""
        try:
            import msal
        except ImportError:
            raise ImportError("msal package required. Install with: pip install msal")

        from dotenv import load_dotenv
        load_dotenv(BASE_DIR / ".env")

        client_id = os.getenv("ONEDRIVE_CLIENT_ID", "")
        client_secret = os.getenv("ONEDRIVE_CLIENT_SECRET", "")

        if not client_id:
            raise ValueError("ONEDRIVE_CLIENT_ID not set in .env")

        # Check for cached token
        cache = msal.SerializableTokenCache()
        if self.credentials_path.exists():
            cache.deserialize(self.credentials_path.read_text())

        app = msal.ConfidentialClientApplication(
            client_id,
            authority="https://login.microsoftonline.com/consumers",
            client_credential=client_secret,
            token_cache=cache,
        )

        scopes = ["https://graph.microsoft.com/Files.ReadWrite"]

        # Try cache first
        accounts = app.get_accounts()
        if accounts:
            result = app.acquire_token_silent(scopes, account=accounts[0])
            if result and "access_token" in result:
                self._save_cache(cache)
                return result["access_token"]

        # Interactive flow
        flow = app.initiate_device_flow(scopes=scopes)
        print(f"\nOneDrive auth: {flow['message']}")

        result = app.acquire_token_by_device_flow(flow)
        if "access_token" not in result:
            raise RuntimeError(f"OneDrive auth failed: {result.get('error_description', 'Unknown error')}")

        self._save_cache(cache)
        return result["access_token"]

    def _save_cache(self, cache):
        self.credentials_path.parent.mkdir(parents=True, exist_ok=True)
        self.credentials_path.write_text(cache.serialize())

    def _headers(self):
        return {"Authorization": f"Bearer {self.token}"}

    def upload(self, local_path: str, remote_name: str) -> str:
        import httpx

        path = f"{self.folder_path}/{remote_name}".replace("//", "/")
        url = f"https://graph.microsoft.com/v1.0/me/drive/root:{path}:/content"

        with open(local_path, "rb") as f:
            resp = httpx.put(url, headers=self._headers(), content=f.read(), timeout=60)

        resp.raise_for_status()
        data = resp.json()
        return data.get("webUrl", data.get("id", ""))

    def download(self, remote_name: str, local_path: str):
        import httpx

        path = f"{self.folder_path}/{remote_name}".replace("//", "/")
        url = f"https://graph.microsoft.com/v1.0/me/drive/root:{path}:/content"

        resp = httpx.get(url, headers=self._headers(), follow_redirects=True, timeout=60)
        resp.raise_for_status()

        with open(local_path, "wb") as f:
            f.write(resp.content)

    def list_files(self, prefix: str = "") -> list:
        import httpx

        path = self.folder_path.replace("//", "/")
        url = f"https://graph.microsoft.com/v1.0/me/drive/root:{path}:/children"

        resp = httpx.get(url, headers=self._headers(), timeout=30)
        resp.raise_for_status()

        files = [item["name"] for item in resp.json().get("value", [])
                 if "file" in item and item["name"].startswith(prefix)]
        return sorted(files)

    def get_share_link(self, remote_name: str) -> str:
        import httpx

        path = f"{self.folder_path}/{remote_name}".replace("//", "/")
        url = f"https://graph.microsoft.com/v1.0/me/drive/root:{path}:/createLink"

        resp = httpx.post(
            url, headers=self._headers(),
            json={"type": "view", "scope": "anonymous"},
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json().get("link", {}).get("webUrl", "")

    def test_connection(self) -> bool:
        import httpx
        try:
            resp = httpx.get(
                "https://graph.microsoft.com/v1.0/me/drive",
                headers=self._headers(), timeout=10,
            )
            return resp.status_code == 200
        except Exception:
            return False
