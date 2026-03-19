"""Google Drive storage adapter."""

import json
import os
from pathlib import Path

from storage.adapter import StorageAdapter, BASE_DIR


class GoogleDriveAdapter(StorageAdapter):
    """Upload/download files to Google Drive."""

    def __init__(self, config: dict):
        self.folder_id = config.get("folder_id", "")
        self.folder_name = config.get("folder_name", "Campaign Respond")
        self.credentials_path = Path(
            config.get("credentials_path",
                       str(BASE_DIR / "storage/credentials/google-token.json"))
        )
        self._service = None

    @property
    def service(self):
        if self._service is None:
            self._service = self._authenticate()
        return self._service

    def _authenticate(self):
        """Authenticate with Google Drive API."""
        try:
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            from google.auth.transport.requests import Request
            from googleapiclient.discovery import build
        except ImportError:
            raise ImportError(
                "Google API packages required. Install with:\n"
                "pip install google-auth-oauthlib google-api-python-client"
            )

        SCOPES = ["https://www.googleapis.com/auth/drive.file"]
        creds = None

        if self.credentials_path.exists():
            creds = Credentials.from_authorized_user_file(
                str(self.credentials_path), SCOPES
            )

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                client_secrets = BASE_DIR / "storage" / "credentials" / "google-client-secrets.json"
                if not client_secrets.exists():
                    raise FileNotFoundError(
                        f"Google client secrets not found at {client_secrets}. "
                        "Download from Google Cloud Console."
                    )
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(client_secrets), SCOPES
                )

                headless = os.getenv("CAMPAIGN_RESPOND_HEADLESS", "").lower() == "true"
                if headless:
                    creds = flow.run_console()
                else:
                    creds = flow.run_local_server(port=0)

            self.credentials_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.credentials_path, "w") as f:
                f.write(creds.to_json())

        return build("drive", "v3", credentials=creds)

    def _ensure_folder(self) -> str:
        """Get or create the Campaign Respond folder."""
        if self.folder_id:
            return self.folder_id

        # Search for existing folder
        results = self.service.files().list(
            q=f"name='{self.folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false",
            spaces="drive",
            fields="files(id, name)",
        ).execute()

        files = results.get("files", [])
        if files:
            self.folder_id = files[0]["id"]
            return self.folder_id

        # Create folder
        metadata = {
            "name": self.folder_name,
            "mimeType": "application/vnd.google-apps.folder",
        }
        folder = self.service.files().create(
            body=metadata, fields="id"
        ).execute()
        self.folder_id = folder["id"]
        return self.folder_id

    def upload(self, local_path: str, remote_name: str) -> str:
        from googleapiclient.http import MediaFileUpload

        folder_id = self._ensure_folder()

        metadata = {
            "name": remote_name,
            "parents": [folder_id],
        }
        media = MediaFileUpload(local_path, resumable=True)

        file = self.service.files().create(
            body=metadata, media_body=media, fields="id,webViewLink"
        ).execute()

        return file.get("webViewLink", file.get("id", ""))

    def download(self, remote_name: str, local_path: str):
        from googleapiclient.http import MediaIoBaseDownload
        import io

        # Find file by name
        folder_id = self._ensure_folder()
        results = self.service.files().list(
            q=f"name='{remote_name}' and '{folder_id}' in parents and trashed=false",
            fields="files(id)",
        ).execute()

        files = results.get("files", [])
        if not files:
            raise FileNotFoundError(f"File not found in Drive: {remote_name}")

        request = self.service.files().get_media(fileId=files[0]["id"])
        with open(local_path, "wb") as f:
            downloader = MediaIoBaseDownload(f, request)
            done = False
            while not done:
                _, done = downloader.next_chunk()

    def list_files(self, prefix: str = "") -> list:
        folder_id = self._ensure_folder()
        query = f"'{folder_id}' in parents and trashed=false"
        if prefix:
            query += f" and name contains '{prefix}'"

        results = self.service.files().list(
            q=query, fields="files(name)"
        ).execute()

        return [f["name"] for f in results.get("files", [])]

    def get_share_link(self, remote_name: str) -> str:
        folder_id = self._ensure_folder()
        results = self.service.files().list(
            q=f"name='{remote_name}' and '{folder_id}' in parents and trashed=false",
            fields="files(id,webViewLink)",
        ).execute()

        files = results.get("files", [])
        if not files:
            return ""

        # Make shareable
        self.service.permissions().create(
            fileId=files[0]["id"],
            body={"type": "anyone", "role": "reader"},
        ).execute()

        return files[0].get("webViewLink", "")

    def test_connection(self) -> bool:
        try:
            self.service.files().list(pageSize=1).execute()
            return True
        except Exception:
            return False
