"""Command-line helpers for interacting with Celery workers."""

from __future__ import annotations

import argparse

from workers.tasks import run_backfill, run_daily_sync


def trigger_backfill(site_id: int) -> None:
    result = run_backfill.delay(site_id)
    print(f"Queued backfill task for site {site_id} (task id={result.id})")


def trigger_daily_sync(site_id: int) -> None:
    result = run_daily_sync.delay(site_id)
    print(f"Queued daily sync task for site {site_id} (task id={result.id})")


def refresh_schedule() -> None:
    from workers.celery_app import refresh_periodic_tasks

    refresh_periodic_tasks()
    print("Celery beat schedule refreshed from database state.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Celery worker utilities")
    subparsers = parser.add_subparsers(dest="command", required=True)

    backfill_parser = subparsers.add_parser("backfill", help="Queue a backfill task")
    backfill_parser.add_argument("site_id", type=int)

    sync_parser = subparsers.add_parser("sync", help="Queue a daily sync task")
    sync_parser.add_argument("site_id", type=int)

    subparsers.add_parser(
        "refresh-schedule",
        help="Reload the Celery beat schedule based on enabled sites",
    )

    args = parser.parse_args()
    if args.command == "backfill":
        trigger_backfill(args.site_id)
    elif args.command == "sync":
        trigger_daily_sync(args.site_id)
    elif args.command == "refresh-schedule":
        refresh_schedule()


if __name__ == "__main__":
    main()
