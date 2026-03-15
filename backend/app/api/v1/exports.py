"""
Exports API — v1.

GET /projects/{id}/export/html   Standalone HTML storyboard
GET /projects/{id}/export/json   Raw JSON export
"""
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse, JSONResponse

from app.dependencies import get_store
from app.store.base import BaseStore

router = APIRouter(tags=["Exports"])


@router.get("/projects/{project_id}/export/html")
async def export_html(project_id: str, store: BaseStore = Depends(get_store)):
    """
    Download a self-contained HTML storyboard file.
    All images are base64-embedded — fully portable.
    """
    proj = await store.get_project(project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found.")
    if not proj.storyboard:
        raise HTTPException(status_code=400, detail="Storyboard not ready yet.")

    html_path = proj.storyboard.html_export_path
    if not html_path or not Path(html_path).exists():
        raise HTTPException(
            status_code=404,
            detail="HTML export file not found. Try regenerating the storyboard.",
        )

    safe_title = "".join(c for c in proj.title if c.isalnum() or c in " -_")[:50]
    filename = f"{safe_title.replace(' ', '_')}_storyboard.html"

    return FileResponse(
        path=html_path,
        media_type="text/html",
        filename=filename,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/projects/{project_id}/export/json")
async def export_json(project_id: str, store: BaseStore = Depends(get_store)):
    """Export the full project + storyboard data as JSON."""
    proj = await store.get_project(project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found.")

    # Exclude local file paths from JSON export (not useful outside the server)
    data = proj.model_dump(mode="json")
    if data.get("storyboard") and data["storyboard"].get("panels"):
        for panel in data["storyboard"]["panels"]:
            panel.pop("local_image_path", None)

    safe_title = "".join(c for c in proj.title if c.isalnum() or c in " -_")[:50]
    filename = f"{safe_title.replace(' ', '_')}_data.json"

    return JSONResponse(
        content=data,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )