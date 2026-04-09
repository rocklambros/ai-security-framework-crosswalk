"""Smoke test: verify the Dash app creates without error."""
import pytest


def test_create_app_import():
    """App module is importable."""
    from app.dash_app.app import create_app
    assert callable(create_app)


def test_create_app_returns_dash_instance():
    """create_app() returns a Dash app with the expected layout."""
    from app.dash_app.app import create_app
    app = create_app()
    assert app.title == "AI Security Framework Crosswalk"
    assert app.layout is not None


def test_about_page_layout():
    """About page layout returns an HTML component."""
    from app.dash_app.pages.about import layout
    result = layout()
    assert result is not None
