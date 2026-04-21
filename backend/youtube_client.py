import re
from typing import Any


# ── helpers ──────────────────────────────────────────────────────────────────

def _parse_iso_duration(iso: str) -> int:
    """Return total seconds for an ISO 8601 duration string (e.g. PT1M30S)."""
    m = re.fullmatch(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso or "")
    if not m:
        return 0
    h, mn, s = (int(x or 0) for x in m.groups())
    return h * 3600 + mn * 60 + s


def _col(headers: list[str], name: str) -> int:
    return headers.index(name)


# ── channel info ─────────────────────────────────────────────────────────────

def fetch_all_channels_for_account(youtube) -> list[dict]:
    resp = youtube.channels().list(
        part="snippet,statistics,contentDetails",
        mine=True,
        maxResults=50,
    ).execute()
    return [_parse_channel_item(i) for i in resp.get("items", [])]


def fetch_channel_info(youtube, channel_id: str) -> dict:
    resp = youtube.channels().list(
        part="snippet,statistics,contentDetails",
        id=channel_id,
    ).execute()
    items = resp.get("items", [])
    if not items:
        raise ValueError(f"Channel {channel_id} not found")
    return _parse_channel_item(items[0])


def _parse_channel_item(item: dict) -> dict:
    stats = item.get("statistics", {})
    return {
        "id": item["id"],
        "title": item["snippet"]["title"],
        "thumbnail": item["snippet"]["thumbnails"].get("default", {}).get("url", ""),
        "subscriberCount": int(stats.get("subscriberCount", 0)),
        "viewCount": int(stats.get("viewCount", 0)),
        "videoCount": int(stats.get("videoCount", 0)),
        "uploadsPlaylistId": item["contentDetails"]["relatedPlaylists"]["uploads"],
    }


# ── video counts (LF / SF) ────────────────────────────────────────────────────

def fetch_video_counts(youtube, uploads_playlist_id: str) -> dict:
    """Return {lf, sf, total} by inspecting every video's duration."""
    video_ids: list[str] = []
    page_token = None
    while True:
        resp = youtube.playlistItems().list(
            part="contentDetails",
            playlistId=uploads_playlist_id,
            maxResults=50,
            pageToken=page_token,
        ).execute()
        video_ids += [i["contentDetails"]["videoId"] for i in resp.get("items", [])]
        page_token = resp.get("nextPageToken")
        if not page_token:
            break

    lf = sf = 0
    for i in range(0, len(video_ids), 50):
        batch = video_ids[i : i + 50]
        resp = youtube.videos().list(
            part="contentDetails",
            id=",".join(batch),
        ).execute()
        for item in resp.get("items", []):
            secs = _parse_iso_duration(item["contentDetails"]["duration"])
            if secs <= 60:
                sf += 1
            else:
                lf += 1

    return {"lf": lf, "sf": sf, "total": lf + sf}


# ── analytics ─────────────────────────────────────────────────────────────────

def fetch_channel_analytics(analytics, channel_id: str, start_date: str, end_date: str) -> dict:
    """
    Returns aggregated analytics + per-day trend for the channel.
    Metrics: views, impressions, CTR, avgViewDuration, avgViewPercentage,
             subscribersGained, subscribersLost.
    """
    metrics = (
        "views,"
        "estimatedMinutesWatched,"
        "averageViewDuration,"
        "averageViewPercentage,"
        "impressions,"
        "impressionClickThroughRate,"
        "subscribersGained,"
        "subscribersLost"
    )
    try:
        resp = analytics.reports().query(
            ids=f"channel=={channel_id}",
            startDate=start_date,
            endDate=end_date,
            metrics=metrics,
            dimensions="day",
            sort="day",
        ).execute()
    except Exception as e:
        return _empty_analytics(str(e))

    headers = [c["name"] for c in resp.get("columnHeaders", [])]
    rows: list[list[Any]] = resp.get("rows", [])
    if not rows:
        return _empty_analytics()

    def g(row, name, cast=float):
        return cast(row[_col(headers, name)])

    total_views = sum(g(r, "views", int) for r in rows)
    total_impressions = sum(g(r, "impressions", int) for r in rows)
    total_subs_gained = sum(g(r, "subscribersGained", int) for r in rows)
    total_subs_lost = sum(g(r, "subscribersLost", int) for r in rows)

    avg_view_dur = (
        sum(g(r, "averageViewDuration") * g(r, "views", int) for r in rows) / total_views
        if total_views else 0
    )
    avg_view_pct = (
        sum(g(r, "averageViewPercentage") * g(r, "views", int) for r in rows) / total_views
        if total_views else 0
    )
    avg_ctr = (
        sum(g(r, "impressionClickThroughRate") * g(r, "impressions", int) for r in rows)
        / total_impressions
        if total_impressions else 0
    )

    trend = [
        {
            "date": r[_col(headers, "day")],
            "views": g(r, "views", int),
            "impressions": g(r, "impressions", int),
        }
        for r in rows
    ]

    return {
        "views": total_views,
        "impressions": total_impressions,
        "subscribersGained": total_subs_gained,
        "subscribersLost": total_subs_lost,
        "netSubscribers": total_subs_gained - total_subs_lost,
        "avgViewDuration": round(avg_view_dur),
        "avgViewPercentage": round(avg_view_pct, 2),
        "ctr": round(avg_ctr * 100, 2),
        "trend": trend,
        "error": None,
    }


def fetch_content_type_analytics(analytics, channel_id: str, start_date: str, end_date: str) -> dict:
    """
    Split views into lf_views / sf_views using the contentType dimension.
    Falls back to zeros if the dimension isn't available for the channel.
    """
    try:
        resp = analytics.reports().query(
            ids=f"channel=={channel_id}",
            startDate=start_date,
            endDate=end_date,
            metrics="views",
            dimensions="contentType",
        ).execute()
    except Exception:
        return {"lf_views": 0, "sf_views": 0}

    lf_views = sf_views = 0
    for row in resp.get("rows", []):
        content_type: str = row[0].upper()
        views = int(row[1])
        if "SHORT" in content_type:
            sf_views += views
        else:
            lf_views += views

    return {"lf_views": lf_views, "sf_views": sf_views}


def _empty_analytics(error: str | None = None) -> dict:
    return {
        "views": 0,
        "impressions": 0,
        "subscribersGained": 0,
        "subscribersLost": 0,
        "netSubscribers": 0,
        "avgViewDuration": 0,
        "avgViewPercentage": 0,
        "ctr": 0,
        "lf_views": 0,
        "sf_views": 0,
        "trend": [],
        "error": error,
    }
