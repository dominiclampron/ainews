"""
config/setup.py - Interactive setup wizard for first-run configuration.

Guides users through:
1. Selecting AI provider
2. Entering API key
3. Configuring optional settings
"""
from __future__ import annotations

import sys
from typing import Optional

from config.settings import Settings, AISettings
from config.secrets import set_api_key, has_api_key, mask_api_key, get_api_key


# Provider information
PROVIDERS = {
    "gemini": {
        "name": "Google Gemini",
        "description": "Fast, cost-effective. Recommended for most users.",
        "models": ["gemini-2.5-flash", "gemini-1.5-flash", "gemini-1.5-pro", "gemini-pro"],
        "default_model": "gemini-2.5-flash",
        "key_url": "https://aistudio.google.com/app/apikey",
    },
    "openai": {
        "name": "OpenAI",
        "description": "GPT-4 and ChatGPT. High quality, higher cost.",
        "models": ["gpt-4o-mini", "gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"],
        "default_model": "gpt-4o-mini",
        "key_url": "https://platform.openai.com/api-keys",
    },
    "claude": {
        "name": "Anthropic Claude",
        "description": "Thoughtful, nuanced responses. Good for analysis.",
        "models": ["claude-3-haiku-20240307", "claude-3-sonnet-20240229", "claude-3-opus-20240229"],
        "default_model": "claude-3-haiku-20240307",
        "key_url": "https://console.anthropic.com/settings/keys",
    },
    "local": {
        "name": "Local LLM (Ollama)",
        "description": "Free, private. Requires Ollama installed locally.",
        "models": ["llama2", "mistral", "codellama", "mixtral"],
        "default_model": "llama2",
        "key_url": None,
    },
}


def print_header(title: str):
    """Print a formatted header."""
    print()
    print("=" * 60)
    print(f"  {title}")
    print("=" * 60)


def print_menu(options: list[tuple[str, str]], prompt: str = "Select option") -> str:
    """
    Display a numbered menu and get user selection.
    
    Args:
        options: List of (key, description) tuples
        prompt: Prompt text
        
    Returns:
        Selected key
    """
    print()
    for i, (key, desc) in enumerate(options, 1):
        print(f"  [{i}] {desc}")
    print()
    
    while True:
        try:
            choice = input(f"{prompt} [1-{len(options)}]: ").strip()
            if choice.lower() in ('q', 'quit', 'exit'):
                return None
            idx = int(choice) - 1
            if 0 <= idx < len(options):
                return options[idx][0]
            print(f"  Please enter a number between 1 and {len(options)}")
        except ValueError:
            print("  Invalid input. Enter a number.")
        except (EOFError, KeyboardInterrupt):
            print("\n  Setup cancelled.")
            return None


def setup_provider() -> Optional[tuple[str, str]]:
    """
    Interactive provider selection.
    
    Returns:
        Tuple of (provider_key, model) or None if cancelled
    """
    print_header("SELECT AI PROVIDER")
    print()
    print("  Choose an AI provider for generating summaries and digests.")
    
    options = [
        (key, f"{info['name']} - {info['description']}")
        for key, info in PROVIDERS.items()
    ]
    options.append(("none", "Skip AI features for now"))
    
    provider = print_menu(options, "Select provider")
    
    if not provider or provider == "none":
        return "none", ""
    
    info = PROVIDERS[provider]
    
    # Select model
    print()
    print(f"  Available models for {info['name']}:")
    model_options = [(m, m) for m in info["models"]]
    model = print_menu(model_options, "Select model")
    
    if not model:
        model = info["default_model"]
    
    return provider, model


def setup_api_key(provider: str) -> bool:
    """
    Interactive API key entry.
    
    Args:
        provider: Provider key
        
    Returns:
        True if key was set successfully
    """
    if provider in ("none", "local"):
        return True
    
    info = PROVIDERS.get(provider, {})
    
    print_header("ENTER API KEY")
    print()
    print(f"  Provider: {info.get('name', provider)}")
    
    if info.get("key_url"):
        print(f"  Get your key at: {info['key_url']}")
    
    # Check if key already exists
    existing = get_api_key(provider)
    if existing:
        print(f"  Current key: {mask_api_key(existing)}")
        print()
        change = input("  Change API key? [y/N]: ").strip().lower()
        if change not in ('y', 'yes'):
            return True
    
    print()
    print("  Enter your API key (input is hidden):")
    
    try:
        # Try to use getpass for hidden input
        try:
            import getpass
            api_key = getpass.getpass("  API Key: ")
        except Exception:
            api_key = input("  API Key: ")
        
        if not api_key.strip():
            print("  ⚠️ No key entered. AI features will be disabled.")
            return False
        
        if set_api_key(provider, api_key.strip()):
            print("  ✓ API key saved securely to .env")
            return True
        else:
            print("  ❌ Failed to save API key")
            return False
            
    except (EOFError, KeyboardInterrupt):
        print("\n  Setup cancelled.")
        return False


def setup_wizard() -> Optional[Settings]:
    """
    Run the full interactive setup wizard.
    
    Returns:
        Settings object if completed, None if cancelled
    """
    print_header("NEWS AGGREGATOR - FIRST TIME SETUP")
    print()
    print("  Welcome! Let's configure your news aggregator.")
    print("  This wizard will help you set up AI-powered summaries.")
    print()
    print("  Press Ctrl+C at any time to cancel.")
    
    # Step 1: Select provider
    result = setup_provider()
    if result is None:
        return None
    
    provider, model = result
    
    # Step 2: Enter API key
    if provider not in ("none", "local"):
        if not setup_api_key(provider):
            # Continue without AI
            provider = "none"
            model = ""
    
    # Step 3: Create settings
    settings = Settings(
        ai=AISettings(
            provider=provider,
            model=model,
        ),
        first_run=False,
    )
    
    # Save settings
    if settings.save():
        print_header("SETUP COMPLETE")
        print()
        if provider != "none":
            print(f"  ✓ AI Provider: {PROVIDERS.get(provider, {}).get('name', provider)}")
            print(f"  ✓ Model: {model}")
        else:
            print("  ℹ️ AI features disabled (can be enabled later)")
        print()
        print("  Configuration saved to config/config.json")
        print("  You can modify settings with: python ainews.py --config")
        print()
        return settings
    else:
        print("  ❌ Failed to save configuration")
        return None


def show_status():
    """Display current configuration status."""
    from config.settings import Settings
    
    settings = Settings.load()
    
    print_header("CONFIGURATION STATUS")
    print()
    
    # AI Provider
    if settings.ai.provider == "none":
        print("  AI Provider:    Not configured")
    else:
        info = PROVIDERS.get(settings.ai.provider, {})
        print(f"  AI Provider:    {info.get('name', settings.ai.provider)}")
        print(f"  Model:          {settings.ai.model}")
        
        # API Key status
        if settings.ai.provider != "local":
            key = get_api_key(settings.ai.provider)
            if key:
                print(f"  API Key:        {mask_api_key(key)}")
            else:
                print("  API Key:        ❌ Not set")
    
    # Database
    print()
    print(f"  Database:       {settings.database.path}")
    print(f"  Store articles: {'Yes' if settings.database.store_articles else 'No'}")
    
    # Digest
    print()
    print(f"  Digest freq:    {settings.digest.frequency}")
    print(f"  Auto-generate:  {'Yes' if settings.digest.auto_generate else 'No'}")
    
    # Security check
    from config.secrets import verify_env_security
    security = verify_env_security()
    
    print()
    print("  Security:")
    if security["exists"]:
        print(f"    .env exists:     Yes")
        print(f"    Permissions OK:  {'Yes' if security['permissions_ok'] else 'No'}")
        print(f"    Gitignored:      {'Yes' if security['gitignored'] else 'No'}")
        for warning in security.get("warnings", []):
            print(f"    ⚠️ {warning}")
    else:
        print("    .env:            Not created yet")
    
    print()


if __name__ == "__main__":
    # Allow running setup directly
    setup_wizard()
