import pickle
from pathlib import Path
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

SCOPES = [
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/yt-analytics.readonly",
]

TOKENS_DIR = Path(__file__).parent / "tokens"
CLIENT_SECRETS_FILE = Path(__file__).parent / "client_secret.json"


def _token_path(account_id: str) -> Path:
    TOKENS_DIR.mkdir(exist_ok=True)
    return TOKENS_DIR / f"{account_id}.pickle"


def list_accounts() -> list[str]:
    TOKENS_DIR.mkdir(exist_ok=True)
    return [p.stem for p in sorted(TOKENS_DIR.glob("*.pickle"))]


def load_credentials(account_id: str) -> Credentials | None:
    path = _token_path(account_id)
    if not path.exists():
        return None
    with open(path, "rb") as f:
        creds: Credentials = pickle.load(f)
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        save_credentials(account_id, creds)
    return creds if creds and creds.valid else None


def save_credentials(account_id: str, creds: Credentials) -> None:
    with open(_token_path(account_id), "wb") as f:
        pickle.dump(creds, f)


def delete_credentials(account_id: str) -> bool:
    path = _token_path(account_id)
    if path.exists():
        path.unlink()
        return True
    return False


def create_auth_flow(redirect_uri: str) -> Flow:
    return Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        redirect_uri=redirect_uri,
    )


def get_youtube_service(account_id: str):
    creds = load_credentials(account_id)
    if not creds:
        raise ValueError(f"No valid credentials for account '{account_id}'")
    return build("youtube", "v3", credentials=creds, cache_discovery=False)


def get_analytics_service(account_id: str):
    creds = load_credentials(account_id)
    if not creds:
        raise ValueError(f"No valid credentials for account '{account_id}'")
    return build("youtubeAnalytics", "v2", credentials=creds, cache_discovery=False)
