"""Unit tests for the in-memory store."""
import asyncio
import pytest

from app.models.enums import PanelStatus, ProjectStatus
from app.models.project import GenerationConfig, PanelModel, PanelGenerationMeta, ProjectModel
from app.models.enums import ImageModel, StyleProfile
from app.store.memory_store import InMemoryStore


def make_project(title="Test Project") -> ProjectModel:
    return ProjectModel(
        title=title,
        input_text="Some test input text that is long enough.",
        config=GenerationConfig(
            image_model=ImageModel.DALLE3,
            style_profile=StyleProfile.CINEMATIC,
        ),
    )


def make_panel(index: int, status: PanelStatus = PanelStatus.PENDING) -> PanelModel:
    return PanelModel(
        panel_index=index,
        original_text=f"Text for panel {index}",
        status=status,
        generation_meta=PanelGenerationMeta(model_used=ImageModel.DALLE3),
    )


@pytest.mark.asyncio
class TestInMemoryStore:

    async def test_create_and_get(self):
        store = InMemoryStore()
        proj = make_project()
        await store.create_project(proj)
        retrieved = await store.get_project(proj.project_id)
        assert retrieved is not None
        assert retrieved.project_id == proj.project_id
        assert retrieved.title == "Test Project"

    async def test_get_nonexistent_returns_none(self):
        store = InMemoryStore()
        result = await store.get_project("nonexistent-id")
        assert result is None

    async def test_list_projects_sorted_newest_first(self):
        store = InMemoryStore()
        p1 = make_project("First")
        p2 = make_project("Second")
        p3 = make_project("Third")
        await store.create_project(p1)
        await asyncio.sleep(0.001)
        await store.create_project(p2)
        await asyncio.sleep(0.001)
        await store.create_project(p3)
        projects = await store.list_projects()
        assert projects[0].title == "Third"
        assert projects[-1].title == "First"

    async def test_update_project(self):
        store = InMemoryStore()
        proj = make_project()
        await store.create_project(proj)
        updated = await store.update_project(proj.project_id, status=ProjectStatus.COMPLETED)
        assert updated.status == ProjectStatus.COMPLETED

        refetched = await store.get_project(proj.project_id)
        assert refetched.status == ProjectStatus.COMPLETED

    async def test_update_nonexistent_returns_none(self):
        store = InMemoryStore()
        result = await store.update_project("bad-id", status=ProjectStatus.FAILED)
        assert result is None

    async def test_delete_project(self):
        store = InMemoryStore()
        proj = make_project()
        await store.create_project(proj)
        deleted = await store.delete_project(proj.project_id)
        assert deleted is True
        assert await store.get_project(proj.project_id) is None

    async def test_delete_nonexistent_returns_false(self):
        store = InMemoryStore()
        result = await store.delete_project("ghost-id")
        assert result is False

    async def test_upsert_panel_inserts(self):
        store = InMemoryStore()
        proj = make_project()
        await store.create_project(proj)
        panel = make_panel(0)
        result = await store.upsert_panel(proj.project_id, panel)
        assert result is True

        updated_proj = await store.get_project(proj.project_id)
        assert updated_proj.storyboard is not None
        assert len(updated_proj.storyboard.panels) == 1

    async def test_upsert_panel_replaces(self):
        store = InMemoryStore()
        proj = make_project()
        await store.create_project(proj)
        panel_v1 = make_panel(0, PanelStatus.PENDING)
        panel_v2 = make_panel(0, PanelStatus.DONE)
        await store.upsert_panel(proj.project_id, panel_v1)
        await store.upsert_panel(proj.project_id, panel_v2)
        updated = await store.get_project(proj.project_id)
        assert len(updated.storyboard.panels) == 1
        assert updated.storyboard.panels[0].status == PanelStatus.DONE

    async def test_count(self):
        store = InMemoryStore()
        assert await store.count() == 0
        await store.create_project(make_project())
        await store.create_project(make_project())
        assert await store.count() == 2

    async def test_get_returns_deep_copy(self):
        """Mutations on returned object must not affect stored state."""
        store = InMemoryStore()
        proj = make_project()
        await store.create_project(proj)
        copy1 = await store.get_project(proj.project_id)
        copy1.title = "Mutated"
        copy2 = await store.get_project(proj.project_id)
        assert copy2.title == "Test Project"