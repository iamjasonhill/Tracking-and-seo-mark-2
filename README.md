# SEO Data Sync Platform

This project provides a FastAPI-based backend for managing search console
integrations and scheduled data syncs.  Celery is used to coordinate both the
historical backfill and the daily incremental sync jobs for each site.

## Running the application

1.  Install dependencies:

    ```bash
    pip install -r requirements.txt
    ```

2.  Start the FastAPI server:

    ```bash
    uvicorn app.main:app --reload
    ```

The API expects an `ENCRYPTION_KEY` environment variable containing a
base64-encoded Fernet key. A development-safe default is provided, but you
should generate a unique value for any deployed environment:

```bash
python - <<'PY'
import base64, os
print(base64.urlsafe_b64encode(os.urandom(32)).decode())
PY
```

Set the resulting value before starting the API, worker, or tests:

```bash
export ENCRYPTION_KEY="<generated-key>"
```

## Background workers

Celery powers the asynchronous processing pipeline.  Two processes are required
in development:

- **Worker:** Executes queued backfill and daily sync tasks.
- **Beat:** Enqueues the `run_daily_sync` task for every enabled site once per
  day based on the configured schedule.

Start them with:

```bash
celery -A workers.celery_app worker --loglevel=info
celery -A workers.celery_app beat --loglevel=info
```

The schedule is rebuilt automatically when the beat process starts, but it can
also be refreshed manually:

```bash
python -m workers.cli refresh-schedule
```

## Triggering jobs manually

A small CLI wrapper is available for local workflows.

```bash
python -m workers.cli backfill <site_id>
python -m workers.cli sync <site_id>
```

Both commands enqueue Celery tasks, so make sure the worker process is running.
