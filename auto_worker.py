from pathlib import Path
import argparse
import json
import time
import traceback
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import server
import cloud_tuning


cloud_tuning.install(server)


ROOT = Path(__file__).resolve().parent
CONFIG_PATH = ROOT / "auto_config.json"
LOG_PATH = ROOT / "automation_log.jsonl"


def load_config():
    if not CONFIG_PATH.exists():
        raise RuntimeError("ไม่พบ auto_config.json")
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def append_log(event):
    event = {
        "time": time.strftime("%Y-%m-%d %H:%M:%S"),
        **event,
    }
    with LOG_PATH.open("a", encoding="utf-8") as file:
        file.write(json.dumps(event, ensure_ascii=False) + "\n")


def make_description(story, footer):
    title = story.get("title", "เรื่องผี")
    place = story.get("seed", {}).get("placeTitle") or title
    parts = [
        f"เรื่องหลอนจาก{place}",
        "",
        story.get("script", ""),
        footer or "",
    ]
    return "\n".join(part for part in parts if part is not None).strip()[:4900]


def run_once(upload_override=None):
    config = load_config()
    payload = {
        "mode": config.get("mode", "short"),
        "brief": config.get("brief", ""),
        "count": config.get("count", 1),
    }
    upload_enabled = config.get("uploadToYouTube", False) if upload_override is None else upload_override

    append_log({
        "status": "started",
        "mode": payload["mode"],
        "count": payload["count"],
        "uploadToYouTube": upload_enabled,
    })

    videos = server.render_video_batch(payload)
    results = []
    youtube_config = config.get("youtube", {})

    for index, video in enumerate(videos, start=1):
        story = video["story"]
        video_path = server.RENDERS / video["fileName"]
        item = {
            "index": index,
            "title": story["title"],
            "fileName": video["fileName"],
            "filePath": str(video_path),
            "duration": story.get("targetSeconds"),
        }

        if upload_enabled:
            from youtube_uploader import upload_video

            upload = upload_video(
                video_path,
                title=story["title"],
                description=make_description(story, youtube_config.get("descriptionFooter", "")),
                tags=youtube_config.get("tags", []),
                category_id=youtube_config.get("categoryId", "24"),
                privacy_status=youtube_config.get("privacyStatus", "private"),
                contains_synthetic_media=youtube_config.get("containsSyntheticMedia", True),
            )
            item["youtube"] = upload

        results.append(item)
        append_log({"status": "video_done", **item})

    append_log({"status": "finished", "videos": results})
    return results


def parse_schedule_times(value):
    times = []
    for item in value:
        hour_text, minute_text = item.split(":", 1)
        hour = int(hour_text)
        minute = int(minute_text)
        if not 0 <= hour <= 23 or not 0 <= minute <= 59:
            raise ValueError(f"Invalid schedule time: {item}")
        times.append((hour, minute))
    return sorted(set(times))


def next_scheduled_run(schedule_times, timezone_name):
    timezone = ZoneInfo(timezone_name)
    now = datetime.now(timezone)
    for hour, minute in schedule_times:
        candidate = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if candidate > now:
            return candidate

    first_hour, first_minute = schedule_times[0]
    tomorrow = now + timedelta(days=1)
    return tomorrow.replace(hour=first_hour, minute=first_minute, second=0, microsecond=0)


def run_schedule(upload_override, schedule_times, timezone_name):
    while True:
        run_at = next_scheduled_run(schedule_times, timezone_name)
        wait_seconds = max(1, (run_at - datetime.now(ZoneInfo(timezone_name))).total_seconds())
        append_log({
            "status": "waiting",
            "nextRun": run_at.isoformat(),
            "timezone": timezone_name,
        })
        print(f"Next run: {run_at.isoformat()}", flush=True)
        time.sleep(wait_seconds)

        try:
            results = run_once(upload_override=upload_override)
            print(json.dumps(results, ensure_ascii=False, indent=2), flush=True)
        except Exception as error:
            append_log({
                "status": "failed",
                "error": str(error),
                "traceback": traceback.format_exc(),
            })
            print(f"Scheduled run failed: {error}", flush=True)


def main():
    parser = argparse.ArgumentParser(description="Run Horror AutoFilm automatically.")
    parser.add_argument("--once", action="store_true", help="Create one batch and stop.")
    parser.add_argument("--loop", action="store_true", help="Keep creating batches forever.")
    parser.add_argument("--schedule", action="store_true", help="Run at fixed daily times.")
    parser.add_argument("--schedule-times", nargs="+", default=None, help="Daily run times such as 06:00 11:00 18:00.")
    parser.add_argument("--timezone", default=None, help="IANA timezone for scheduled runs.")
    parser.add_argument("--interval-minutes", type=int, default=360, help="Delay between batches in loop mode.")
    parser.add_argument("--upload", action="store_true", help="Upload to YouTube regardless of config.")
    parser.add_argument("--no-upload", action="store_true", help="Do not upload to YouTube regardless of config.")
    args = parser.parse_args()
    config = load_config()

    if not args.once and not args.loop and not args.schedule:
        args.once = True

    upload_override = None
    if args.upload:
        upload_override = True
    if args.no_upload:
        upload_override = False

    if args.schedule:
        schedule_config = config.get("schedule", {})
        time_values = args.schedule_times or schedule_config.get("times", ["06:00", "11:00", "18:00"])
        timezone_name = args.timezone or schedule_config.get("timezone", "Asia/Bangkok")
        run_schedule(upload_override, parse_schedule_times(time_values), timezone_name)
        return

    while True:
        try:
            results = run_once(upload_override=upload_override)
            print(json.dumps(results, ensure_ascii=False, indent=2))
        except Exception as error:
            append_log({
                "status": "failed",
                "error": str(error),
                "traceback": traceback.format_exc(),
            })
            raise

        if not args.loop:
            break
        time.sleep(max(60, args.interval_minutes * 60))


if __name__ == "__main__":
    main()
