# config/__init__.py
"""
Configuration module - Settings and secrets management.
"""

from config.settings import (
    Settings,
    AISettings,
    DatabaseSettings,
    DigestSettings,
    get_settings,
    reset_settings,
    CONFIG_FILE,
)
from config.secrets import (
    get_api_key,
    set_api_key,
    has_api_key,
    mask_api_key,
    verify_env_security,
    load_dotenv,
)
from config.setup import (
    setup_wizard,
    show_status,
    PROVIDERS,
)

__all__ = [
    # Settings
    "Settings",
    "AISettings",
    "DatabaseSettings",
    "DigestSettings",
    "get_settings",
    "reset_settings",
    "CONFIG_FILE",
    # Secrets
    "get_api_key",
    "set_api_key",
    "has_api_key",
    "mask_api_key",
    "verify_env_security",
    "load_dotenv",
    # Setup
    "setup_wizard",
    "show_status",
    "PROVIDERS",
]

