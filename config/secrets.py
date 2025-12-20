"""
config/secrets.py - Secure API key management.

Handles loading API keys from environment variables or .env file.
NEVER stores keys in plain text in code or config.json.

Security:
- Keys loaded from .env file (gitignored)
- .env file should have 600 permissions (owner-only)
- Keys exposed only via environment variables
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional


# Path to .env file
CONFIG_DIR = Path(__file__).parent.parent
ENV_FILE = CONFIG_DIR / ".env"

# Environment variable names for each provider
ENV_VAR_NAMES = {
    "gemini": "AINEWS_GEMINI_API_KEY",
    "openai": "AINEWS_OPENAI_API_KEY",
    "claude": "AINEWS_CLAUDE_API_KEY",
    "local": None,  # Local doesn't need API key
}

# Alternative env var names (for compatibility)
ALT_ENV_VAR_NAMES = {
    "gemini": ["GOOGLE_API_KEY", "GEMINI_API_KEY"],
    "openai": ["OPENAI_API_KEY"],
    "claude": ["ANTHROPIC_API_KEY"],
}


def load_dotenv() -> bool:
    """
    Load environment variables from .env file.
    
    Returns:
        True if .env was loaded, False if not found
    """
    if not ENV_FILE.exists():
        return False
    
    try:
        # Try to use python-dotenv if available
        try:
            from dotenv import load_dotenv as dotenv_load
            dotenv_load(ENV_FILE)
            return True
        except ImportError:
            pass
        
        # Fallback: manual parsing
        with open(ENV_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    os.environ[key] = value
        
        return True
    except Exception as e:
        print(f"⚠️ Error loading .env: {e}")
        return False


def get_api_key(provider: str) -> Optional[str]:
    """
    Get API key for a provider.
    
    Checks environment variables in order:
    1. AINEWS_{PROVIDER}_API_KEY
    2. Standard provider env vars (e.g., OPENAI_API_KEY)
    3. AINEWS_API_KEY (generic, used by menu setup)
    
    Args:
        provider: Provider name (gemini, openai, claude, local)
        
    Returns:
        API key string or None if not found
    """
    # Ensure .env is loaded
    load_dotenv()
    
    provider = provider.lower()
    
    # Local doesn't need API key
    if provider == "local":
        return "local"
    
    # Check primary env var
    primary_var = ENV_VAR_NAMES.get(provider)
    if primary_var:
        key = os.environ.get(primary_var)
        if key:
            return key
    
    # Check alternative env vars
    alt_vars = ALT_ENV_VAR_NAMES.get(provider, [])
    for var in alt_vars:
        key = os.environ.get(var)
        if key:
            return key
    
    # Check generic AINEWS_API_KEY (used by menu setup)
    generic_key = os.environ.get("AINEWS_API_KEY")
    if generic_key:
        return generic_key
    
    return None


def set_api_key(provider: str, api_key: str) -> bool:
    """
    Save API key to .env file.
    
    Creates .env if it doesn't exist.
    Sets secure file permissions (600).
    
    Args:
        provider: Provider name
        api_key: The API key to store
        
    Returns:
        True if saved successfully
    """
    provider = provider.lower()
    var_name = ENV_VAR_NAMES.get(provider)
    
    if not var_name:
        if provider == "local":
            return True  # No key needed
        return False
    
    try:
        # Read existing .env content
        existing_lines = []
        if ENV_FILE.exists():
            with open(ENV_FILE, "r", encoding="utf-8") as f:
                existing_lines = f.readlines()
        
        # Update or add the key
        key_found = False
        new_lines = []
        for line in existing_lines:
            if line.strip().startswith(f"{var_name}="):
                new_lines.append(f'{var_name}="{api_key}"\n')
                key_found = True
            else:
                new_lines.append(line)
        
        if not key_found:
            new_lines.append(f'{var_name}="{api_key}"\n')
        
        # Write back
        with open(ENV_FILE, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
        
        # Set secure permissions (Unix only)
        try:
            os.chmod(ENV_FILE, 0o600)
        except (OSError, AttributeError):
            pass  # Windows doesn't support chmod
        
        # Update current environment
        os.environ[var_name] = api_key
        
        return True
        
    except Exception as e:
        print(f"❌ Error saving API key: {e}")
        return False


def delete_api_key(provider: str) -> bool:
    """
    Remove API key from .env file.
    
    Args:
        provider: Provider name
        
    Returns:
        True if removed successfully
    """
    provider = provider.lower()
    var_name = ENV_VAR_NAMES.get(provider)
    
    if not var_name or not ENV_FILE.exists():
        return True
    
    try:
        with open(ENV_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        new_lines = [
            line for line in lines 
            if not line.strip().startswith(f"{var_name}=")
        ]
        
        with open(ENV_FILE, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
        
        # Remove from current environment
        if var_name in os.environ:
            del os.environ[var_name]
        
        return True
        
    except Exception as e:
        print(f"❌ Error removing API key: {e}")
        return False


def has_api_key(provider: str) -> bool:
    """
    Check if API key is configured for a provider.
    
    Args:
        provider: Provider name
        
    Returns:
        True if key is set
    """
    return get_api_key(provider) is not None


def mask_api_key(key: str, visible_chars: int = 4) -> str:
    """
    Mask API key for display.
    
    Args:
        key: The API key
        visible_chars: Number of characters to show at end
        
    Returns:
        Masked string like "***...abc123"
    """
    if not key:
        return "(not set)"
    if len(key) <= visible_chars:
        return "*" * len(key)
    return "*" * 8 + "..." + key[-visible_chars:]


def verify_env_security() -> dict:
    """
    Check security status of .env file.
    
    Returns:
        Dict with security check results
    """
    result = {
        "exists": ENV_FILE.exists(),
        "permissions_ok": False,
        "gitignored": False,
        "warnings": [],
    }
    
    if not result["exists"]:
        return result
    
    # Check permissions (Unix)
    try:
        stat = os.stat(ENV_FILE)
        mode = stat.st_mode & 0o777
        result["permissions_ok"] = mode <= 0o600
        if not result["permissions_ok"]:
            result["warnings"].append(
                f".env has permissions {oct(mode)}, should be 600"
            )
    except (OSError, AttributeError):
        result["permissions_ok"] = True  # Assume OK on Windows
    
    # Check if .gitignore includes .env
    gitignore_path = CONFIG_DIR / ".gitignore"
    if gitignore_path.exists():
        with open(gitignore_path, "r") as f:
            content = f.read()
            result["gitignored"] = ".env" in content
    
    if not result["gitignored"]:
        result["warnings"].append(".env may not be in .gitignore!")
    
    return result
