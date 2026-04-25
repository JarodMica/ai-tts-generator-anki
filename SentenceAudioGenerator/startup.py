from __future__ import annotations

from aqt import gui_hooks, mw
from aqt.browser import Browser
from aqt.qt import QAction
from aqt.utils import qconnect

from .batch import run_bulk_add_tts
from .config import ensure_user_dirs
from .config_dialog import show_config_dialog


def setup_addon() -> None:
    ensure_user_dirs()
    mw.addonManager.setConfigAction(__name__, show_config_dialog)
    gui_hooks.browser_menus_did_init.append(on_browser_menus_did_init)


def on_browser_menus_did_init(browser: Browser) -> None:
    action = QAction("Bulk add TTS", browser)
    qconnect(action.triggered, lambda: run_bulk_add_tts(browser))
    browser.form.menuEdit.addSeparator()
    browser.form.menuEdit.addAction(action)
