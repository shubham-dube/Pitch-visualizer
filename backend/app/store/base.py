"""
Abstract store interface. InMemoryStore implements this.
To add MongoDB later: create MongoStore(BaseStore) and swap in dependencies.py.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional

from app.models.project import PanelModel, ProjectModel


class BaseStore(ABC):

    @abstractmethod
    async def create_project(self, project: ProjectModel) -> ProjectModel:
        ...

    @abstractmethod
    async def get_project(self, project_id: str) -> Optional[ProjectModel]:
        ...

    @abstractmethod
    async def list_projects(self) -> List[ProjectModel]:
        ...

    @abstractmethod
    async def update_project(self, project_id: str, **updates) -> Optional[ProjectModel]:
        """Apply keyword updates to a project's top-level fields."""
        ...

    @abstractmethod
    async def delete_project(self, project_id: str) -> bool:
        ...

    @abstractmethod
    async def upsert_panel(
        self, project_id: str, panel: PanelModel
    ) -> bool:
        """Insert or replace a panel by panel_index."""
        ...