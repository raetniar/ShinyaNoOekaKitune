"""Fetch public metadata only; replace recommendations only after both tabs succeed."""
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from yt_dlp import YoutubeDL

ROOT = Path(__file__).resolve().parents[1]
CHANNEL = "https://www.youtube.com/@uiko_uka"


def select(entries, category):
    videos = []
    seen = set()
    for entry in entries:
        video_id = entry.get("id", "")
        if not re.fullmatch(r"[A-Za-z0-9_-]{11}", video_id) or video_id in seen:
            continue
        views = entry.get("view_count")
        # Hidden/unavailable counts must never be converted to zero.
        if not isinstance(views, (int, float)) or views < 0:
            views = None
        seen.add(video_id)
        videos.append({"id": video_id, "views": int(views) if views is not None else None})
    if not videos:
        raise ValueError(f"No public {category} metadata; retaining previous file")
    latest = videos[:5]  # YouTube's channel tab is extracted in newest-first order.
    ranked = [item for item in videos if item["views"] is not None]
    if len(ranked) < min(5, len(videos)):
        raise ValueError(f"Insufficient public view counts for {category}; retaining previous file")
    popular = sorted(ranked, key=lambda item: item["views"], reverse=True)[:5]
    ids = list(dict.fromkeys(item["id"] for item in latest + popular))
    url = (lambda value: f"https://www.youtube.com/shorts/{value}") if category == "shorts" else (lambda value: f"https://youtu.be/{value}")
    return [url(value) for value in ids], {"latest": [x["id"] for x in latest], "popular": [x["id"] for x in popular], "publicCount": len(videos), "unavailableViewCounts": len(videos) - len(ranked)}


def main():
    output = {}
    details = {}
    options = {"extract_flat": True, "skip_download": True, "ignoreerrors": False, "quiet": True, "socket_timeout": 30, "retries": 3, "extractor_retries": 3}
    with YoutubeDL(options) as ydl:
        for category, tab in (("shorts", "shorts"), ("videos", "videos")):
            result = ydl.extract_info(f"{CHANNEL}/{tab}", download=False)
            if not result or result.get("availability") in ("private", "needs_auth"):
                raise ValueError("Public channel metadata unavailable")
            output[category], details[category] = select(list(result.get("entries") or []), category)
    output["updatedAt"] = datetime.now(timezone.utc).isoformat()
    output["selection"] = details
    target = ROOT / "assets/recommendations.js"
    temporary = target.with_suffix(".js.tmp")
    temporary.write_text("// Generated from public channel tabs: newest five + most-viewed five.\nwindow.UIKO_RECOMMENDATIONS = " + json.dumps(output, ensure_ascii=True, indent=2) + ";\n", encoding="utf-8")
    temporary.replace(target)
    print(json.dumps({"updatedAt": output["updatedAt"], "selection": details}))


if __name__ == "__main__":
    main()

