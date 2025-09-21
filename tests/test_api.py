from datetime import datetime, timezone


def test_user_crud_flow(client):
    response = client.post(
        "/api/v1/users/",
        json={"email": "user@example.com", "password": "secret"},
    )
    assert response.status_code == 201
    user = response.json()
    assert user["email"] == "user@example.com"

    list_response = client.get("/api/v1/users/")
    assert list_response.status_code == 200
    users = list_response.json()
    assert len(users) == 1

    detail_response = client.get(f"/api/v1/users/{user['id']}")
    assert detail_response.status_code == 200

    update_response = client.put(
        f"/api/v1/users/{user['id']}",
        json={"email": "updated@example.com"},
    )
    assert update_response.status_code == 200
    updated_user = update_response.json()
    assert updated_user["email"] == "updated@example.com"

    delete_response = client.delete(f"/api/v1/users/{user['id']}")
    assert delete_response.status_code == 200


def test_account_crud_flow(client):
    user = client.post(
        "/api/v1/users/",
        json={"email": "owner@example.com", "password": "secret"},
    ).json()

    create_response = client.post(
        "/api/v1/accounts/",
        json={
            "user_id": user["id"],
            "provider": "Google",
            "credentials": {"token": "abc"},
        },
    )
    assert create_response.status_code == 201
    account = create_response.json()
    assert account["provider"] == "google"
    assert account["user_id"] == user["id"]

    list_response = client.get(f"/api/v1/accounts/?user_id={user['id']}")
    assert list_response.status_code == 200
    accounts = list_response.json()
    assert len(accounts) == 1

    update_response = client.put(
        f"/api/v1/accounts/{account['id']}",
        json={"provider": "BING"},
    )
    assert update_response.status_code == 200
    assert update_response.json()["provider"] == "bing"

    delete_response = client.delete(f"/api/v1/accounts/{account['id']}")
    assert delete_response.status_code == 200


def test_account_rejects_unknown_provider(client):
    user = client.post(
        "/api/v1/users/",
        json={"email": "invalid-provider@example.com", "password": "secret"},
    ).json()

    response = client.post(
        "/api/v1/accounts/",
        json={
            "user_id": user["id"],
            "provider": "yahoo",
            "credentials": {"token": "zzz"},
        },
    )
    assert response.status_code == 422
    list_response = client.get(f"/api/v1/accounts/?user_id={user['id']}")
    assert list_response.status_code == 200
    assert list_response.json() == []


def test_site_and_sync_job_crud_flow(client):
    user = client.post(
        "/api/v1/users/",
        json={"email": "sync@example.com", "password": "secret"},
    ).json()
    account = client.post(
        "/api/v1/accounts/",
        json={
            "user_id": user["id"],
            "provider": "Google",
            "credentials": {"token": "xyz"},
        },
    ).json()

    site_response = client.post(
        "/api/v1/sites/",
        json={"account_id": account["id"], "site_url": "https://example.com"},
    )
    assert site_response.status_code == 201
    site = site_response.json()
    assert site["site_url"] == "https://example.com"

    sites_response = client.get(f"/api/v1/sites/?account_id={account['id']}")
    assert sites_response.status_code == 200
    assert len(sites_response.json()) == 1

    site_update = client.put(
        f"/api/v1/sites/{site['id']}",
        json={"enabled": False},
    )
    assert site_update.status_code == 200
    assert site_update.json()["enabled"] is False

    sync_job_response = client.post(
        "/api/v1/sync-jobs/",
        json={
            "site_id": site["id"],
            "status": "pending",
            "started_at": datetime.now(timezone.utc).isoformat(),
        },
    )
    assert sync_job_response.status_code == 201
    sync_job = sync_job_response.json()
    assert sync_job["status"] == "pending"

    sync_jobs_response = client.get("/api/v1/sync-jobs/?status_filter=pending")
    assert sync_jobs_response.status_code == 200
    assert len(sync_jobs_response.json()) == 1

    sync_job_update = client.put(
        f"/api/v1/sync-jobs/{sync_job['id']}",
        json={"status": "completed"},
    )
    assert sync_job_update.status_code == 200
    assert sync_job_update.json()["status"] == "completed"

    sync_job_delete = client.delete(f"/api/v1/sync-jobs/{sync_job['id']}")
    assert sync_job_delete.status_code == 200

    site_delete = client.delete(f"/api/v1/sites/{site['id']}")
    assert site_delete.status_code == 200
