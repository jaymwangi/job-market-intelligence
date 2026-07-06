from .about import render as render_about
from .analytics import render as render_analytics
from .jobs import render as render_jobs
from .overview import render as render_overview

__all__ = [
    "render_overview",
    "render_jobs",
    "render_analytics",
    "render_about",
]
