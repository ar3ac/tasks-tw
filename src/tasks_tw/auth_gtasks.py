from __future__ import annotations

import json
import os
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = [
    "https://www.googleapis.com/auth/tasks.readonly"
]  # cambia a tasks se ti serve scrittura


def _default_token_path() -> Path:
    if os.name == "nt":
        base = Path(os.environ.get("APPDATA", Path.home()))
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return base / "tasks-tw" / "token.json"


def load_or_login(*, client_secrets_path: Path, token_path: Path) -> Credentials:
    creds: Credentials | None = None

    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                str(client_secrets_path), SCOPES
            )
            creds = flow.run_local_server(port=0)

        token_path.parent.mkdir(parents=True, exist_ok=True)
        token_path.write_text(creds.to_json(), encoding="utf-8")

    return creds


def gtasks():
    client_secrets_path = Path("client_secret.json")
    token_path = _default_token_path()

    if not client_secrets_path.exists():
        raise SystemExit(
            f"File mancante: {client_secrets_path}\n"
            "Metti qui il JSON OAuth (Desktop app) scaricato da Google Cloud."
        )

    creds = load_or_login(
        client_secrets_path=client_secrets_path, token_path=token_path
    )

    service = build("tasks", "v1", credentials=creds)

    # Smoke test: lista delle tasklist
    resp = service.tasklists().list(maxResults=20).execute()
    items = resp.get("items", [])

    print(f"OK: autenticato. Tasklists trovate: {len(items)}")
    for tl in items[:10]:
        if "To Do" in tl.get("title", ""):
            print(f"- {tl.get('title')}  ({tl.get('id')})")
            tasks_resp = (
                service.tasks()
                .list(
                    tasklist=tl.get("id"),  # tasks.list richiede tasklistId [page:10]
                    showCompleted=False,  # utile per widget (solo aperti) [page:10]
                    maxResults=100,  # max 100 [page:10]
                )
                .execute()
            )
            print(f"  Tasks aperti: {tasks_resp.get('items', [])}\n\n")
            return tasks_resp.get("items", [])


if __name__ == "__main__":
    gtasks()
