"""
Integration tests for the REST API.
All external AI calls are mocked — no real API keys needed.
"""
from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient

from app.main import create_app
from app.models.enums import ImageModel, ProjectStatus, StyleProfile
from app.store.memory_store import InMemoryStore


@pytest.fixture
def app():
    application = create_app()
    application.state.store = InMemoryStore()
    return application


@pytest.fixture
def client(app):
    with TestClient(app) as c:
        yield c


# ── Health ────────────────────────────────────────────────────────

class TestHealth:
    def test_health_returns_200(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "uptime_seconds" in data

    def test_root_returns_200(self, client):
        resp = client.get("/")
        assert resp.status_code == 200
        assert "docs" in resp.json()


# ── Styles & Models ───────────────────────────────────────────────

class TestStyles:
    def test_list_styles_returns_all(self, client):
        resp = client.get("/api/v1/styles")
        assert resp.status_code == 200
        styles = resp.json()
        assert len(styles) == 6
        ids = [s["id"] for s in styles]
        assert "cinematic" in ids
        assert "corporate" in ids

    def test_list_models_returns_both(self, client):
        resp = client.get("/api/v1/models")
        assert resp.status_code == 200
        models = resp.json()
        assert len(models) == 2
        ids = [m["id"] for m in models]
        assert "dalle3" in ids
        assert "gemini" in ids


# ── Projects ──────────────────────────────────────────────────────

class TestCreateProject:
    def test_create_returns_202(self, client):
        with patch("app.api.v1.projects.StoryboardPipeline") as mock_pipeline_cls:
            resp = client.post("/api/v1/projects", json={
                "title": "Test Storyboard",
                "input_text": "This is a test narrative that is long enough to be valid for testing the system.",
                "style_profile": "cinematic",
                "options": {"max_panels": 3, "image_model": "dalle3"},
            })
        assert resp.status_code == 202
        data = resp.json()
        assert "project_id" in data
        assert data["status"] == "queued"
        assert data["title"] == "Test Storyboard"
        assert "poll_url" in data

    def test_create_rejects_short_text(self, client):
        resp = client.post("/api/v1/projects", json={
            "title": "Bad",
            "input_text": "Too short.",
            "style_profile": "cinematic",
        })
        assert resp.status_code == 422

    def test_create_rejects_empty_title(self, client):
        resp = client.post("/api/v1/projects", json={
            "title": "",
            "input_text": "This is a sufficiently long text input for testing purposes here.",
            "style_profile": "cinematic",
        })
        assert resp.status_code == 422

    def test_create_rejects_invalid_style(self, client):
        resp = client.post("/api/v1/projects", json={
            "title": "Test",
            "input_text": "This is a sufficiently long text input for testing purposes here.",
            "style_profile": "nonexistent_style",
        })
        assert resp.status_code == 422


class TestListProjects:
    def test_empty_list(self, client):
        resp = client.get("/api/v1/projects")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_project_appears_after_creation(self, client):
        client.post("/api/v1/projects", json={
            "title": "Appears in List",
            "input_text": "This is a sufficiently long text that appears in the list endpoint for testing.",
            "style_profile": "corporate",
        })
        resp = client.get("/api/v1/projects")
        assert resp.status_code == 200
        titles = [p["title"] for p in resp.json()]
        assert "Appears in List" in titles


class TestGetProject:
    def test_get_existing_project(self, client):
        create_resp = client.post("/api/v1/projects", json={
            "title": "Fetch Me",
            "input_text": "This is a sufficiently long text input for testing GET endpoint.",
            "style_profile": "minimal",
        })
        project_id = create_resp.json()["project_id"]

        resp = client.get(f"/api/v1/projects/{project_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["project_id"] == project_id
        assert data["title"] == "Fetch Me"

    def test_get_nonexistent_returns_404(self, client):
        resp = client.get("/api/v1/projects/nonexistent-id-xyz")
        assert resp.status_code == 404


class TestProjectStatus:
    def test_status_of_queued_project(self, client):
        create_resp = client.post("/api/v1/projects", json={
            "title": "Status Test",
            "input_text": "This is a sufficiently long text input for status polling test.",
            "style_profile": "cinematic",
        })
        pid = create_resp.json()["project_id"]

        resp = client.get(f"/api/v1/projects/{pid}/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["project_id"] == pid
        assert data["status"] in ["queued", "generating", "completed", "failed"]
        assert "progress" in data
        assert isinstance(data["completed_panels"], list)

    def test_status_404_for_unknown(self, client):
        resp = client.get("/api/v1/projects/unknown-xyz/status")
        assert resp.status_code == 404


class TestDeleteProject:
    def test_delete_returns_204(self, client):
        create_resp = client.post("/api/v1/projects", json={
            "title": "Delete Me",
            "input_text": "This text is long enough to pass the validation check for deletion test.",
            "style_profile": "storybook",
        })
        pid = create_resp.json()["project_id"]

        del_resp = client.delete(f"/api/v1/projects/{pid}")
        assert del_resp.status_code == 204

        get_resp = client.get(f"/api/v1/projects/{pid}")
        assert get_resp.status_code == 404

    def test_delete_nonexistent_returns_404(self, client):
        resp = client.delete("/api/v1/projects/ghost-id-xyz")
        assert resp.status_code == 404


# ── Exports ───────────────────────────────────────────────────────

class TestExports:
    def test_json_export_404_for_missing_project(self, client):
        resp = client.get("/api/v1/projects/missing/export/json")
        assert resp.status_code == 404

    def test_html_export_400_when_storyboard_not_ready(self, client):
        create_resp = client.post("/api/v1/projects", json={
            "title": "Export Test",
            "input_text": "This is long enough text for testing export endpoint availability.",
            "style_profile": "cinematic",
        })
        pid = create_resp.json()["project_id"]
        # Storyboard won't be ready immediately (async background task)
        resp = client.get(f"/api/v1/projects/{pid}/export/html")
        assert resp.status_code in (400, 404)