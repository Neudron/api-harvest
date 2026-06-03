"""Tests for entry-point handler plugin loading (offline, in-process fakes)."""

from __future__ import annotations

import pytest

from harvest.handlers import HANDLER_REGISTRY, load_plugin_handlers
from harvest.handlers.base import Handler


class _PluginHandler(Handler):
    pass


class _OtherPluginHandler(Handler):
    pass


class _FakeEntryPoint:
    def __init__(self, name: str, obj, *, raises: bool = False):
        self.name = name
        self._obj = obj
        self._raises = raises

    def load(self):
        if self._raises:
            raise ImportError("broken plugin")
        return self._obj


@pytest.fixture(autouse=True)
def _restore_registry():
    """Snapshot and restore the global registry around each test."""
    snapshot = dict(HANDLER_REGISTRY)
    yield
    HANDLER_REGISTRY.clear()
    HANDLER_REGISTRY.update(snapshot)


def test_loads_new_plugin_slug() -> None:
    eps = [_FakeEntryPoint("my-cool-provider", _PluginHandler)]
    added = load_plugin_handlers(entry_points_fn=lambda: eps)
    assert added == ["my-cool-provider"]
    assert HANDLER_REGISTRY["my-cool-provider"] is _PluginHandler


def test_core_wins_slug_collision() -> None:
    # 'groq' is a built-in handler; a plugin claiming it must be ignored.
    assert "groq" in HANDLER_REGISTRY
    core_cls = HANDLER_REGISTRY["groq"]
    eps = [_FakeEntryPoint("groq", _PluginHandler)]
    added = load_plugin_handlers(entry_points_fn=lambda: eps)
    assert added == []
    assert HANDLER_REGISTRY["groq"] is core_cls  # unchanged


def test_broken_plugin_is_skipped() -> None:
    eps = [
        _FakeEntryPoint("broken", _PluginHandler, raises=True),
        _FakeEntryPoint("works", _OtherPluginHandler),
    ]
    added = load_plugin_handlers(entry_points_fn=lambda: eps)
    assert added == ["works"]
    assert "broken" not in HANDLER_REGISTRY
    assert HANDLER_REGISTRY["works"] is _OtherPluginHandler


def test_entry_points_source_error_is_swallowed() -> None:
    def boom():
        raise RuntimeError("metadata blew up")

    # Must not raise; returns nothing added.
    added = load_plugin_handlers(entry_points_fn=boom)
    assert added == []


def test_unnamed_entry_point_skipped() -> None:
    eps = [_FakeEntryPoint("", _PluginHandler)]
    added = load_plugin_handlers(entry_points_fn=lambda: eps)
    assert added == []
