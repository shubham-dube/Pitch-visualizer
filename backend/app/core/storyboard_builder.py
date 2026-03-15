"""
Stage 6 — Storyboard Assembly.

Builds the final StoryboardModel from completed panels
and generates a standalone HTML export (all images base64-embedded).
"""
from __future__ import annotations

import base64
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.models.enums import ArcType, StyleProfile
from app.models.project import PanelModel, StoryboardModel
from app.utils.logger import get_logger

logger = get_logger(__name__)


def _encode_image_b64(path: str) -> Optional[str]:
    """Base64-encode an image file for HTML embedding."""
    try:
        data = Path(path).read_bytes()
        return base64.b64encode(data).decode("utf-8")
    except Exception as exc:
        logger.warning("Could not encode image for export", path=path, error=str(exc))
        return None


class StoryboardBuilder:
    """Assembles panels into a StoryboardModel and generates HTML exports."""

    def __init__(self, templates_dir: str) -> None:
        self._env = Environment(
            loader=FileSystemLoader(templates_dir),
            autoescape=select_autoescape(["html"]),
        )

    def assemble(
        self,
        panels: List[PanelModel],
        overall_arc: ArcType,
        html_export_path: Optional[str] = None,
    ) -> StoryboardModel:
        """Build the StoryboardModel from a list of completed panels."""
        sorted_panels = sorted(panels, key=lambda p: p.panel_index)

        storyboard = StoryboardModel(
            panels=sorted_panels,
            overall_arc=overall_arc,
            html_export_path=html_export_path,
            assembled_at=datetime.now(timezone.utc),
        )

        logger.info(
            "Storyboard assembled",
            panel_count=len(sorted_panels),
            overall_arc=overall_arc.value,
        )
        return storyboard

    def generate_html_export(
        self,
        storyboard: StoryboardModel,
        title: str,
        style_profile: StyleProfile,
        export_path: Path,
    ) -> str:
        """
        Render a self-contained HTML storyboard file with base64 images.
        Returns the path to the generated file.
        """
        # Embed images as base64 for a fully portable file
        panels_data = []
        for panel in storyboard.panels:
            b64 = _encode_image_b64(panel.local_image_path) if panel.local_image_path else None
            panels_data.append({
                "panel": panel,
                "image_b64": b64,
            })

        try:
            template = self._env.get_template("storyboard_export.html")
        except Exception:
            # Fallback: inline template if file not found
            logger.warning("Template file not found, using inline fallback")
            return self._render_fallback_html(
                title, style_profile, storyboard, panels_data, export_path
            )

        html = template.render(
            title=title,
            style_profile=style_profile.value,
            storyboard=storyboard,
            panels_data=panels_data,
            generated_at=datetime.now(timezone.utc).strftime("%B %d, %Y at %H:%M UTC"),
        )

        export_path.parent.mkdir(parents=True, exist_ok=True)
        export_path.write_text(html, encoding="utf-8")
        logger.info("HTML export generated", path=str(export_path))
        return str(export_path)

    def _render_fallback_html(
        self,
        title: str,
        style_profile: StyleProfile,
        storyboard: StoryboardModel,
        panels_data: list,
        export_path: Path,
    ) -> str:
        panel_html_parts = []
        for item in panels_data:
            p = item["panel"]
            b64 = item["image_b64"]
            img_src = f"data:image/png;base64,{b64}" if b64 else ""
            palette_chips = "".join(
                f'<span style="display:inline-block;width:20px;height:20px;border-radius:50%;'
                f'background:{c};margin:2px"></span>'
                for c in p.color_palette
            )
            panel_html_parts.append(f"""
            <div class="panel">
                {'<img src="' + img_src + '" alt="Panel ' + str(p.panel_index+1) + '">' if img_src else '<div class="no-image">Image unavailable</div>'}
                <div class="panel-body">
                    <div class="panel-meta">
                        <span class="role-badge">{p.panel_role.value}</span>
                        <span class="emotion-badge">{p.dominant_emotion.value}</span>
                        <span class="intensity">Intensity {int(p.intensity*100)}%</span>
                    </div>
                    <h3 class="scene-title">{p.scene_title}</h3>
                    <p class="caption">{p.original_text}</p>
                    <div class="palette">{palette_chips}</div>
                </div>
            </div>""")

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} — Pitch Visualizer</title>
<style>
  :root {{
    --primary: #0F172A; --accent: #6366F1; --surface: #1E293B;
    --text: #CBD5E1; --text-muted: #64748B; --border: #334155;
  }}
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ background:var(--primary); color:var(--text); font-family:system-ui,sans-serif; padding:40px 20px; }}
  .header {{ text-align:center; margin-bottom:60px; border-bottom:2px solid var(--accent); padding-bottom:30px; }}
  .header h1 {{ font-size:2.5rem; color:#fff; margin-bottom:8px; }}
  .header .meta {{ color:var(--text-muted); font-size:.9rem; }}
  .arc-banner {{ text-align:center; background:var(--surface); border:1px solid var(--border);
    border-radius:12px; padding:16px 24px; margin-bottom:40px; display:inline-block; }}
  .arc-banner span {{ color:var(--accent); font-weight:600; }}
  .panels {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(480px,1fr)); gap:32px; max-width:1400px; margin:0 auto; }}
  .panel {{ background:var(--surface); border-radius:16px; overflow:hidden; border:1px solid var(--border); }}
  .panel img {{ width:100%; aspect-ratio:16/9; object-fit:cover; display:block; }}
  .no-image {{ width:100%; aspect-ratio:16/9; background:#1a1a2e; display:flex; align-items:center; justify-content:center; color:var(--text-muted); }}
  .panel-body {{ padding:20px; }}
  .panel-meta {{ display:flex; gap:8px; margin-bottom:12px; flex-wrap:wrap; }}
  .role-badge,.emotion-badge {{ background:rgba(99,102,241,.15); color:var(--accent); padding:4px 10px; border-radius:20px; font-size:.75rem; text-transform:uppercase; letter-spacing:.05em; }}
  .intensity {{ color:var(--text-muted); font-size:.75rem; padding:4px 10px; }}
  .scene-title {{ font-size:1.1rem; font-weight:700; color:#fff; margin-bottom:8px; }}
  .caption {{ color:var(--text-muted); font-size:.85rem; line-height:1.6; margin-bottom:12px; }}
  .palette {{ display:flex; gap:4px; }}
  .footer {{ text-align:center; margin-top:60px; padding-top:20px; border-top:1px solid var(--border); color:var(--text-muted); font-size:.8rem; }}
</style>
</head>
<body>
  <div class="header">
    <h1>{title}</h1>
    <p class="meta">Generated with Pitch Visualizer · Style: {style_profile.value} · {len(panels_data)} panels</p>
  </div>
  <div style="text-align:center;margin-bottom:40px">
    <div class="arc-banner">Narrative Arc: <span>{storyboard.overall_arc.value.replace("_"," ").title()}</span></div>
  </div>
  <div class="panels">
    {''.join(panel_html_parts)}
  </div>
  <div class="footer">Created with Pitch Visualizer AI · {datetime.now(timezone.utc).strftime("%B %d, %Y")}</div>
</body>
</html>"""

        export_path.parent.mkdir(parents=True, exist_ok=True)
        export_path.write_text(html, encoding="utf-8")
        logger.info("Fallback HTML export written", path=str(export_path))
        return str(export_path)