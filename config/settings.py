"""
config/settings.py - Configuration management for News Aggregator.

Handles loading and saving user configuration from config.json.
Provides Settings dataclass with all configurable options.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional, Literal


# Configuration file paths
PROJECT_ROOT = Path(__file__).parent.parent
CONFIG_DIR = Path(__file__).parent  # config/ directory
CONFIG_FILE = CONFIG_DIR / "config.json"  # config/config.json
ENV_FILE = PROJECT_ROOT / ".env"


def _migrate_old_configs():
    """Migrate config files from root to config/ if needed (v0.7.2+)."""
    import shutil
    
    # Migrate config.json
    old_config = PROJECT_ROOT / "config.json"
    if old_config.exists() and not CONFIG_FILE.exists():
        shutil.move(str(old_config), str(CONFIG_FILE))
        print("📦 Migrated config.json → config/config.json")
    
    # Migrate presets.json
    old_presets = PROJECT_ROOT / "presets.json"
    new_presets = CONFIG_DIR / "presets.json"
    if old_presets.exists() and not new_presets.exists():
        shutil.move(str(old_presets), str(new_presets))
        print("📦 Migrated presets.json → config/presets.json")


# Run migration on import
_migrate_old_configs()


# Supported AI providers
AIProvider = Literal["gemini", "openai", "claude", "local", "none"]

# Summary length options
SummaryLength = Literal["short", "medium", "long"]

# Digest frequency options
DigestFrequency = Literal["daily", "weekly", "monthly"]


@dataclass
class AISettings:
    """
    AI provider configuration.
    
    Attributes:
        provider: AI service to use (gemini, openai, claude, local, none)
        model: Specific model name (e.g., gemini-1.5-flash, gpt-4o-mini)
        endpoint: Custom API endpoint (for local LLMs or proxies)
        summary_length: Desired summary length
        max_tokens: Maximum tokens for responses
    """
    provider: AIProvider = "none"
    model: str = ""
    endpoint: Optional[str] = None
    summary_length: SummaryLength = "medium"
    max_tokens: int = 1000
    
    def __post_init__(self):
        # Set default models based on provider
        if not self.model and self.provider != "none":
            self.model = self.get_default_model()
    
    def get_default_model(self) -> str:
        """Get default model for the selected provider."""
        defaults = {
            "gemini": "gemini-2.5-flash",
            "openai": "gpt-4o-mini",
            "claude": "claude-3-haiku-20240307",
            "local": "llama2",
            "none": "",
        }
        return defaults.get(self.provider, "")
    
    def is_configured(self) -> bool:
        """Check if AI is configured and ready to use."""
        return self.provider != "none" and bool(self.model)


@dataclass
class DatabaseSettings:
    """
    Database configuration.
    
    Attributes:
        path: Path to SQLite database file
        store_articles: Whether to persist articles to database
        store_summaries: Whether to persist AI summaries
        max_age_days: Delete articles older than this (0 = keep forever)
    """
    path: str = "ainews.db"
    store_articles: bool = True
    store_summaries: bool = True
    max_age_days: int = 90
    
    def get_full_path(self) -> Path:
        """Get absolute path to database file."""
        # Support Docker volume mounts via env var
        env_path = os.environ.get("AINEWS_DB_PATH")
        if env_path:
            return Path(env_path)
        if os.path.isabs(self.path):
            return Path(self.path)
        return PROJECT_ROOT / self.path


@dataclass
class DigestSettings:
    """
    Digest generation configuration.
    
    Attributes:
        frequency: How often to generate digests
        auto_generate: Generate digest automatically after aggregation
        include_summaries: Include AI summaries in digest
        output_format: Output format (markdown, html, text)
    """
    frequency: DigestFrequency = "weekly"
    auto_generate: bool = False
    include_summaries: bool = True
    output_format: Literal["markdown", "html", "text"] = "markdown"


@dataclass
class Settings:
    """
    Main settings container.
    
    Combines all configuration sections into a single object.
    Handles loading from and saving to config.json.
    
    Example:
        >>> settings = Settings.load()
        >>> settings.ai.provider = "gemini"
        >>> settings.save()
    """
    ai: AISettings = field(default_factory=AISettings)
    database: DatabaseSettings = field(default_factory=DatabaseSettings)
    digest: DigestSettings = field(default_factory=DigestSettings)
    
    # Metadata
    version: str = "0.6"
    first_run: bool = True
    
    @classmethod
    def load(cls) -> "Settings":
        """
        Load settings from config.json.
        
        Creates default settings if file doesn't exist.
        
        Returns:
            Settings object with loaded or default values
        """
        if not CONFIG_FILE.exists():
            # Return defaults and mark as first run
            return cls(first_run=True)
        
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            return cls(
                ai=AISettings(**data.get("ai", {})),
                database=DatabaseSettings(**data.get("database", {})),
                digest=DigestSettings(**data.get("digest", {})),
                version=data.get("version", "0.6"),
                first_run=data.get("first_run", False),
            )
        except (json.JSONDecodeError, TypeError) as e:
            print(f"⚠️ Error loading config: {e}")
            return cls(first_run=True)
    
    def save(self) -> bool:
        """
        Save settings to config.json.
        
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            data = {
                "ai": asdict(self.ai),
                "database": asdict(self.database),
                "digest": asdict(self.digest),
                "version": self.version,
                "first_run": self.first_run,
            }
            
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            
            return True
        except Exception as e:
            print(f"❌ Error saving config: {e}")
            return False
    
    def is_ai_ready(self) -> bool:
        """Check if AI features are configured and ready."""
        from config.secrets import get_api_key
        
        if not self.ai.is_configured():
            return False
        
        # Check for API key (not needed for local)
        if self.ai.provider != "local":
            key = get_api_key(self.ai.provider)
            if not key:
                return False
        
        return True


def get_settings() -> Settings:
    """
    Get current settings (convenience function).
    
    Returns:
        Settings object loaded from config.json
    """
    return Settings.load()


def reset_settings() -> Settings:
    """
    Reset settings to defaults.
    
    Returns:
        Fresh Settings object with defaults
    """
    settings = Settings(first_run=True)
    settings.save()
    return settings
