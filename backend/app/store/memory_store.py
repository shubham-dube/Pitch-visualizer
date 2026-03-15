"""
Thread-safe in-memory store backed by a plain Python dict.
Implements BaseStore so it's trivially swappable for MongoDB.
Uses asyncio.Lock for safe concurrent access under FastAPI's async loop.
"""
from __future__ import annotations

import asyncio
import copy
from typing import List, Optional

from app.models.project import PanelModel, ProjectModel, StoryboardModel
from app.store.base import BaseStore


class InMemoryStore(BaseStore):
    """Session-scoped in-memory project store."""

    def __init__(self) -> None:
        self._projects: dict[str, ProjectModel] = {}
        self._lock = asyncio.Lock()

    # ── Create ─────────────────────────────────────────────────────
    async def create_project(self, project: ProjectModel) -> ProjectModel:
        async with self._lock:
            self._projects[project.project_id] = project
        return project

    # ── Read ───────────────────────────────────────────────────────
    async def get_project(self, project_id: str) -> Optional[ProjectModel]:
        async with self._lock:
            proj = self._projects.get(project_id)
            # Return a deep copy so callers don't mutate shared state accidentally
            return copy.deepcopy(proj) if proj else None

    async def list_projects(self) -> List[ProjectModel]:
        async with self._lock:
            # Newest first
            projects = list(self._projects.values())
        return sorted(
            [copy.deepcopy(p) for p in projects],
            key=lambda p: p.created_at,
            reverse=True,
        )

    # ── Update ─────────────────────────────────────────────────────
    async def update_project(self, project_id: str, **updates) -> Optional[ProjectModel]:
        async with self._lock:
            proj = self._projects.get(project_id)
            if not proj:
                return None
            for key, value in updates.items():
                if hasattr(proj, key):
                    setattr(proj, key, value)
            proj.touch()
            return copy.deepcopy(proj)

    # ── Delete ─────────────────────────────────────────────────────
    async def delete_project(self, project_id: str) -> bool:
        async with self._lock:
            if project_id in self._projects:
                del self._projects[project_id]
                return True
            return False

    # ── Panel upsert ───────────────────────────────────────────────
    async def upsert_panel(self, project_id: str, panel: PanelModel) -> bool:
        async with self._lock:
            proj = self._projects.get(project_id)
            if not proj:
                return False

            # Ensure storyboard exists
            if proj.storyboard is None:
                proj.storyboard = StoryboardModel()

            # Replace or append
            panels = proj.storyboard.panels
            for i, existing in enumerate(panels):
                if existing.panel_index == panel.panel_index:
                    panels[i] = panel
                    proj.touch()
                    return True

            panels.append(panel)
            proj.touch()
            return True

    # ── Convenience ────────────────────────────────────────────────
    async def count(self) -> int:
        async with self._lock:
            return len(self._projects)