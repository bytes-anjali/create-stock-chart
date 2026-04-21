import os
from datetime import date, timedelta
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from auth import (
    create_auth_flow,
    delete_credentials,
    get_analytics_service,
    get_youtube_service,
    list_accounts,
    load_credentials,
    save_credentials,
)
from youtube_client import (
    fetch_all_channels_for_account,
    fetch_channel_analytics,
    fetch_channel_info,
    fetch_content_type_analytics,
    fetch_video_counts,
)

load_dotenv()

REDIRECT_URI = os.getenv("REDIRECT_URI", "http://localhost:8000/api/auth/callback")
FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")

app = FastAPI(title="YT Multi-Channel Dashboard", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_ORIGIN, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── accounts ──────────────────────────────────────────────────────────────────

@app.get("/api/accounts")
def get_accounts():
    result = []
    for account_id in list_accounts():
        creds = load_credentials(account_id)
        result.append({"id": account_id, "valid": creds is not None})
    return result


@app.delete("/api/accounts/{account_id}")
def remove_account(account_id: str):
    deleted = delete_credentials(account_id)
    if not deleted:
        raise HTTPException(404, "Account not found")
    return {"status": "deleted"}


# ── oauth ─────────────────────────────────────────────────────────────────────

@app.get("/api/auth/url")
def get_auth_url(account_id: str = Query(..., description="Friendly name for this Google account")):
    if not Path("client_secret.json").exists() and not (Path(__file__).parent / "client_secret.json").exists():
        raise HTTPException(400, "client_secret.json not found in backend/")
    flow = create_auth_flow(REDIRECT_URI)
    auth_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        state=account_id,
        prompt="consent",
    )
    return {"url": auth_url}


@app.get("/api/auth/callback")
def auth_callback(code: str, state: str):
    account_id = state
    flow = create_auth_flow(REDIRECT_URI)
    flow.fetch_token(code=code)
    save_credentials(account_id, flow.credentials)
    return RedirectResponse(url=f"{FRONTEND_ORIGIN}?auth=success&account={account_id}")


# ── channels ──────────────────────────────────────────────────────────────────

@app.get("/api/channels")
def get_channels():
    all_channels = []
    for account_id in list_accounts():
        try:
            youtube = get_youtube_service(account_id)
            for ch in fetch_all_channels_for_account(youtube):
                all_channels.append({**ch, "accountId": account_id})
        except Exception as exc:
            all_channels.append({"accountId": account_id, "error": str(exc)})
    return all_channels


# ── dashboard ─────────────────────────────────────────────────────────────────

@app.get("/api/dashboard")
def get_dashboard(
    channel_ids: str = Query(..., description="Comma-separated channel IDs"),
    start_date: str = Query(default=None),
    end_date: str = Query(default=None),
    include_video_counts: bool = Query(default=True),
):
    if not start_date:
        start_date = (date.today() - timedelta(days=28)).isoformat()
    if not end_date:
        end_date = date.today().isoformat()

    ids = [c.strip() for c in channel_ids.split(",") if c.strip()]

    # Build channel_id -> account_id map
    channel_account_map: dict[str, str] = {}
    for account_id in list_accounts():
        try:
            youtube = get_youtube_service(account_id)
            for ch in fetch_all_channels_for_account(youtube):
                channel_account_map[ch["id"]] = account_id
        except Exception:
            pass

    channel_results = []

    for channel_id in ids:
        account_id = channel_account_map.get(channel_id)
        if not account_id:
            channel_results.append({"id": channel_id, "error": "Account not found or not authenticated"})
            continue

        try:
            youtube = get_youtube_service(account_id)
            analytics = get_analytics_service(account_id)

            info = fetch_channel_info(youtube, channel_id)
            base_analytics = fetch_channel_analytics(analytics, channel_id, start_date, end_date)
            content_split = fetch_content_type_analytics(analytics, channel_id, start_date, end_date)

            video_counts = {"lf": 0, "sf": 0, "total": 0}
            if include_video_counts:
                video_counts = fetch_video_counts(youtube, info["uploadsPlaylistId"])

            channel_results.append({
                **info,
                "accountId": account_id,
                "videos": video_counts,
                "analytics": {**base_analytics, **content_split},
            })
        except Exception as exc:
            channel_results.append({"id": channel_id, "accountId": account_id, "error": str(exc)})

    cumulative = _aggregate(channel_results)

    return {
        "channels": channel_results,
        "cumulative": cumulative,
        "period": {"start": start_date, "end": end_date},
    }


def _aggregate(channels: list[dict]) -> dict:
    valid = [c for c in channels if "error" not in c and "analytics" in c]
    if not valid:
        return {}

    total_views = sum(c["analytics"]["views"] for c in valid)
    total_impressions = sum(c["analytics"]["impressions"] for c in valid)
    total_subs_gained = sum(c["analytics"]["subscribersGained"] for c in valid)
    total_subs_lost = sum(c["analytics"]["subscribersLost"] for c in valid)
    total_lf_views = sum(c["analytics"]["lf_views"] for c in valid)
    total_sf_views = sum(c["analytics"]["sf_views"] for c in valid)
    total_lf_videos = sum(c["videos"]["lf"] for c in valid)
    total_sf_videos = sum(c["videos"]["sf"] for c in valid)
    total_subscribers = sum(c["subscriberCount"] for c in valid)

    avg_ctr = (
        sum(c["analytics"]["ctr"] * c["analytics"]["impressions"] for c in valid) / total_impressions
        if total_impressions else 0
    )
    avg_avp = (
        sum(c["analytics"]["avgViewPercentage"] * c["analytics"]["views"] for c in valid) / total_views
        if total_views else 0
    )
    avg_avd = (
        sum(c["analytics"]["avgViewDuration"] * c["analytics"]["views"] for c in valid) / total_views
        if total_views else 0
    )

    # Merge daily trends
    trend_map: dict[str, dict] = {}
    for c in valid:
        for entry in c["analytics"].get("trend", []):
            d = entry["date"]
            if d not in trend_map:
                trend_map[d] = {"date": d, "views": 0, "impressions": 0}
            trend_map[d]["views"] += entry["views"]
            trend_map[d]["impressions"] += entry["impressions"]

    return {
        "views": total_views,
        "lf_views": total_lf_views,
        "sf_views": total_sf_views,
        "impressions": total_impressions,
        "subscribers": total_subscribers,
        "subscribersGained": total_subs_gained,
        "subscribersLost": total_subs_lost,
        "netSubscribers": total_subs_gained - total_subs_lost,
        "videos": {"lf": total_lf_videos, "sf": total_sf_videos, "total": total_lf_videos + total_sf_videos},
        "ctr": round(avg_ctr, 2),
        "avgViewPercentage": round(avg_avp, 2),
        "avgViewDuration": round(avg_avd),
        "trend": sorted(trend_map.values(), key=lambda x: x["date"]),
    }
