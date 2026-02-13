from __future__ import annotations

"""Configuration and constants for the Tapudsou project."""

from dataclasses import dataclass
import json
import os
from pathlib import Path


SERVICE_ID: str = "tapudsou"
APP_NAME: str = f"local.{SERVICE_ID}"

# Package directory is ``tapudsou/``, project root is its parent.
PACKAGE_DIR: Path = Path(__file__).resolve().parent
BASE_DIR: Path = PACKAGE_DIR.parent

CONFIG_FILE: Path = BASE_DIR / "tapudsou_config.json"

API_BASE_URL: str = os.getenv("TAPUDSOU_API_BASE_URL", "https://api.innovorder.fr")
BRAND_ID: int = int(os.getenv("TAPUDSOU_BRAND_ID", "1249"))
RECHARGE_URL: str = os.getenv(
    "TAPUDSOU_RECHARGE_URL",
    f"https://ewallet.innovorder.fr/{BRAND_ID}/home",
)

DEFAULT_LANGUAGE: str = os.getenv("TAPUDSOU_LANG", "en")


@dataclass
class UserConfig:
    """User-level configuration loaded from a small JSON file.

    Attributes:
        language: ISO language code used for user-facing messages (e.g. ``\"en\"`` or
            ``\"fr\"``).
    """

    language: str = DEFAULT_LANGUAGE


def load_user_config() -> UserConfig:
    """Load the user configuration if available.

    Returns:
        A :class:`UserConfig` instance. If the configuration file does not exist
        or is invalid, defaults are returned.
    """

    if not CONFIG_FILE.exists():
        return UserConfig()

    try:
        raw = CONFIG_FILE.read_text(encoding="utf-8")
        data = json.loads(raw)
    except (OSError, json.JSONDecodeError):
        return UserConfig()

    language = str(data.get("language", DEFAULT_LANGUAGE))
    return UserConfig(language=language)


def save_user_config(config: UserConfig) -> None:
    """Persist the user configuration to disk.

    Args:
        config: Configuration instance to serialize.
    """

    payload = {"language": config.language}
    CONFIG_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

