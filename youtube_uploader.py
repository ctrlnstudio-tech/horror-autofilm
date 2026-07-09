from pathlib import Path
import os
import time


ROOT = Path(__file__).resolve().parent
CLIENT_SECRETS = ROOT / "client_secrets.json"
TOKEN_FILE = ROOT / "youtube_token.json"
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def materialize_secret_file(path, env_name):
    value = os.environ.get(env_name)
    if value and not path.exists():
        path.write_text(value, encoding="utf-8")


def build_youtube_service():
    try:
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.auth.transport.requests import Request
        from googleapiclient.discovery import build
    except ImportError as error:
        raise RuntimeError(
            "ยังไม่ได้ติดตั้ง YouTube upload dependencies: "
            "pip install -r requirements-youtube.txt"
        ) from error

    materialize_secret_file(CLIENT_SECRETS, "YOUTUBE_CLIENT_SECRETS_JSON")
    materialize_secret_file(TOKEN_FILE, "YOUTUBE_TOKEN_JSON")

    credentials = None
    if TOKEN_FILE.exists():
        credentials = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    if credentials and credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())

    if not credentials or not credentials.valid:
        if not CLIENT_SECRETS.exists():
            raise RuntimeError(
                "ยังไม่มี client_secrets.json สำหรับ YouTube OAuth "
                "ต้องสร้าง OAuth client จาก Google Cloud ก่อน"
            )
        flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRETS), SCOPES)
        credentials = flow.run_local_server(port=0)
        TOKEN_FILE.write_text(credentials.to_json(), encoding="utf-8")

    return build("youtube", "v3", credentials=credentials)


def upload_video(file_path, title, description, tags=None, category_id="24", privacy_status="private", contains_synthetic_media=True):
    try:
        from googleapiclient.http import MediaFileUpload
        from googleapiclient.errors import HttpError
    except ImportError as error:
        raise RuntimeError(
            "ยังไม่ได้ติดตั้ง YouTube upload dependencies: "
            "pip install -r requirements-youtube.txt"
        ) from error

    path = Path(file_path)
    if not path.exists():
        raise RuntimeError(f"ไม่พบไฟล์วิดีโอ: {path}")

    youtube = build_youtube_service()
    body = {
        "snippet": {
            "title": title[:100],
            "description": description,
            "tags": tags or [],
            "categoryId": category_id,
        },
        "status": {
            "privacyStatus": privacy_status,
            "selfDeclaredMadeForKids": False,
            "containsSyntheticMedia": contains_synthetic_media,
        },
    }

    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=MediaFileUpload(str(path), chunksize=-1, resumable=True),
    )

    response = None
    retry = 0
    while response is None:
        try:
            _, response = request.next_chunk()
        except HttpError as error:
            if error.resp.status not in (500, 502, 503, 504):
                raise
            retry += 1
            if retry > 8:
                raise
            time.sleep(min(60, 2 ** retry))

    video_id = response.get("id")
    if not video_id:
        raise RuntimeError(f"YouTube upload failed: {response}")
    return {
        "id": video_id,
        "url": f"https://www.youtube.com/watch?v={video_id}",
    }
