import os

os.environ["SECRET_KEY"] = "test-secret-key-not-for-production"  # noqa: S105
os.environ["DATABASE_URL"] = "sqlite:///./test.db"

import pytest
from fastapi.testclient import TestClient

from app.database import Base, engine
from app.main import app


@pytest.fixture()
def client():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as c:
        yield c


def register_and_login(client: TestClient, email: str = "user@example.com") -> dict[str, str]:
    resp = client.post("/auth/register", json={"email": email, "password": "s3curePassw0rd"})
    assert resp.status_code == 201
    resp = client.post("/auth/token", data={"username": email, "password": "s3curePassw0rd"})
    assert resp.status_code == 200
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_health(client: TestClient):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_register_rejects_weak_password(client: TestClient):
    resp = client.post("/auth/register", json={"email": "a@example.com", "password": "short"})
    assert resp.status_code == 422


def test_login_wrong_password(client: TestClient):
    register_and_login(client)
    resp = client.post(
        "/auth/token", data={"username": "user@example.com", "password": "wrongpassword"}
    )
    assert resp.status_code == 401


def test_tasks_require_auth(client: TestClient):
    assert client.get("/tasks").status_code == 401
    assert client.post("/tasks", json={"title": "x"}).status_code == 401


def test_task_crud(client: TestClient):
    headers = register_and_login(client)
    resp = client.post("/tasks", json={"title": "Buy milk"}, headers=headers)
    assert resp.status_code == 201
    task_id = resp.json()["id"]

    resp = client.get("/tasks", headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 1

    resp = client.patch(f"/tasks/{task_id}", json={"done": True}, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["done"] is True

    resp = client.delete(f"/tasks/{task_id}", headers=headers)
    assert resp.status_code == 204


def test_task_isolation_between_users(client: TestClient):
    headers_a = register_and_login(client, "a@example.com")
    headers_b = register_and_login(client, "b@example.com")

    resp = client.post("/tasks", json={"title": "private"}, headers=headers_a)
    task_id = resp.json()["id"]

    assert client.get(f"/tasks/{task_id}", headers=headers_b).status_code == 404
    assert client.delete(f"/tasks/{task_id}", headers=headers_b).status_code == 404
