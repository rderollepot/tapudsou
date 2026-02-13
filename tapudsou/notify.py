from __future__ import annotations

"""Notification helpers for Tapudsou.

Notifications are intentionally kept simple: they use Tkinter when available and
fall back to console output in headless environments.
"""

from tkinter import Tk
from tkinter.messagebox import showinfo
from typing import Final
import webbrowser

from .config import RECHARGE_URL


_LANG_STRINGS: Final[dict[str, dict[str, str]]] = {
    "en": {
        "pwd_not_found": "Could not find a stored password for {username}.",
        "low_balance": "Your canteen card has {balance:.2f}€ left (threshold: {threshold:.2f}€).",
        "title": "Tapudsou",
    },
    "fr": {
        "pwd_not_found": "Impossible de trouver le mot de passe pour {username}.",
        "low_balance": "Il reste {balance:.2f}€ sur ta carte de cantine (seuil: {threshold:.2f}€).",
        "title": "Tapudsou",
    },
}


def _get_message(language: str, key: str, **kwargs: object) -> str:
    """Return a localized message for the given key."""

    language_map = _LANG_STRINGS.get(language, _LANG_STRINGS["en"])
    template = language_map.get(key, key)
    return template.format(**kwargs)


def _safe_message_box(title: str, text: str) -> None:
    """Display a message box when possible, fallback to console otherwise."""

    try:
        root = Tk()
        root.withdraw()
        showinfo(title, text)
        root.destroy()
    except Exception:
        # Fallback mode: headless environment or Tkinter not available.
        print(f"{title}: {text}")


def notify_password_missing(username: str, language: str) -> None:
    """Notify the user that no password could be retrieved from the keyring."""

    title = _get_message(language, "title")
    text = _get_message(language, "pwd_not_found", username=username)
    _safe_message_box(title, text)


def notify_low_balance(balance_eur: float, threshold_eur: float, language: str) -> None:
    """Notify the user that the balance is below the configured threshold.

    Besides displaying a message box, this also opens the Innovorder recharge
    portal in the default web browser.
    """

    title = _get_message(language, "title")
    text = _get_message(
        language,
        "low_balance",
        balance=balance_eur,
        threshold=threshold_eur,
    )
    _safe_message_box(title, text)
    webbrowser.open_new_tab(RECHARGE_URL)

