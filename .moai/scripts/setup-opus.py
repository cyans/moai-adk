#!/usr/bin/env python3
r"""Claude Opus Model Setup Script for MoAI-ADK

Configures Claude Opus model by setting API key and model name.

Usage:
    python setup-opus.py <api-key>
    python setup-opus.py  # Uses default key from .env.opus

Behavior:
    Updates C:\Users\cyan9\.claude\settings.json with Opus API key and model
"""

import json
import sys
from pathlib import Path

# Default Opus API key - Replace with your actual key
DEFAULT_API_KEY = "YOUR_ANTHROPIC_API_KEY_HERE"
DEFAULT_MODEL = "claude-opus-4-5-20251101"


def setup_opus(api_key: str) -> bool:
    """Configure Claude Opus model
    
    Args:
        api_key: Anthropic API key
    
    Returns:
        True if successful, False otherwise
    """
    settings_path = Path(r"C:\Users\cyan9\.claude\settings.json")
    
    try:
        # Load existing settings
        if settings_path.exists():
            with open(settings_path, "r", encoding="utf-8") as f:
                settings = json.load(f)
        else:
            # Create settings if it doesn't exist
            settings_path.parent.mkdir(parents=True, exist_ok=True)
            settings = {}
        
        # Set Opus environment variables
        settings["env"] = {
            "ANTHROPIC_AUTH_TOKEN": api_key,
            "ANTHROPIC_DEFAULT_OPUS_MODEL": DEFAULT_MODEL
        }
        
        # Write back to file
        with open(settings_path, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2)
        
        print(f"✓ Claude Opus configuration updated in: {settings_path}")
        print()
        print("Configured environment variables:")
        print(f"   • ANTHROPIC_AUTH_TOKEN: {api_key[:20]}...")
        print(f"   • ANTHROPIC_DEFAULT_OPUS_MODEL: {DEFAULT_MODEL}")
        print()
        print("✓ Claude Opus configuration complete!")
        
        return True
    
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON in {settings_path}")
        print(f"   Details: {e}")
        return False
    
    except Exception as e:
        print(f"❌ Error during Opus configuration: {e}")
        return False


def main() -> None:
    """Main entry point"""
    # Get API key from command line argument or use default
    if len(sys.argv) >= 2:
        api_key = sys.argv[1]
    else:
        api_key = DEFAULT_API_KEY
        print(f"✓ Using default Anthropic API key")
    
    # Validate key (basic check)
    if not api_key or len(api_key) < 10:
        print("❌ Error: API key appears to be invalid (too short)")
        sys.exit(1)
    
    success = setup_opus(api_key)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
