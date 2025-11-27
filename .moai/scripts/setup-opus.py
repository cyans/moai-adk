#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""Claude Opus Model Setup Script for MoAI-ADK

Configures Claude Opus model by setting API key and model name.

Usage:
    python setup-opus.py <api-key>
    python setup-opus.py  # Uses default key from .env.opus

Behavior:
    Updates global and project-level settings with Opus API key and model
    Removes GLM-specific settings from both global and project settings
"""

import json
import os
import sys
from pathlib import Path

# Windows UTF-8 인코딩 설정
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    os.environ['PYTHONUTF8'] = '1'
    try:
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        if hasattr(sys.stderr, 'reconfigure'):
            sys.stderr.reconfigure(encoding='utf-8', errors='replace')
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            kernel32.SetConsoleOutputCP(65001)  # UTF-8
            kernel32.SetConsoleCP(65001)
        except Exception:
            pass
    except Exception:
        pass

# Default Opus API key - Replace with your actual key
DEFAULT_API_KEY = "YOUR_ANTHROPIC_API_KEY_HERE"
DEFAULT_MODEL = "claude-opus-4-5-20251101"


def setup_opus(api_key: str, project_root: Path | None = None) -> bool:
    """Configure Claude Opus model
    
    Args:
        api_key: Anthropic API key
        project_root: Project root directory (default: current directory)
    
    Returns:
        True if successful, False otherwise
    """
    if project_root is None:
        project_root = Path.cwd()
    else:
        project_root = Path(project_root).resolve()
    
    try:
        # 1. Delete .env.glm if it exists (GLM configuration file)
        env_glm_path = project_root / ".env.glm"
        if env_glm_path.exists():
            env_glm_path.unlink()
            print(f"[OK] Deleted GLM configuration file: {env_glm_path.relative_to(project_root)}")
        
        # 2. Update global settings (user-level)
        global_settings_path = Path.home() / ".claude" / "settings.json"
        
        if global_settings_path.exists():
            with open(global_settings_path, "r", encoding="utf-8") as f:
                global_settings = json.load(f)
        else:
            global_settings_path.parent.mkdir(parents=True, exist_ok=True)
            global_settings = {}
        
        # Set Opus environment variables in global settings
        if "env" not in global_settings:
            global_settings["env"] = {}
        
        global_settings["env"]["ANTHROPIC_AUTH_TOKEN"] = api_key
        global_settings["env"]["ANTHROPIC_DEFAULT_OPUS_MODEL"] = DEFAULT_MODEL
        
        # Remove GLM-specific settings from global settings
        if "ANTHROPIC_BASE_URL" in global_settings.get("env", {}):
            del global_settings["env"]["ANTHROPIC_BASE_URL"]
        if "ANTHROPIC_DEFAULT_HAIKU_MODEL" in global_settings.get("env", {}):
            del global_settings["env"]["ANTHROPIC_DEFAULT_HAIKU_MODEL"]
        if "ANTHROPIC_DEFAULT_SONNET_MODEL" in global_settings.get("env", {}):
            del global_settings["env"]["ANTHROPIC_DEFAULT_SONNET_MODEL"]
        
        # Write back to global settings file
        with open(global_settings_path, "w", encoding="utf-8") as f:
            json.dump(global_settings, f, indent=2, ensure_ascii=False)
        
        print(f"[OK] Deleted GLM configuration file: {env_glm_path.relative_to(project_root)}")
        
        # 3. Update project-level settings.local.json (remove GLM settings)
        local_settings_path = project_root / ".claude" / "settings.local.json"
        
        if local_settings_path.exists():
            with open(local_settings_path, "r", encoding="utf-8") as f:
                local_settings = json.load(f)
            
            modified = False
            
            # Remove GLM-specific environment variables
            if "env" in local_settings:
                # Remove GLM-specific settings
                if "ANTHROPIC_BASE_URL" in local_settings["env"]:
                    del local_settings["env"]["ANTHROPIC_BASE_URL"]
                    modified = True
                if "ANTHROPIC_DEFAULT_HAIKU_MODEL" in local_settings["env"]:
                    del local_settings["env"]["ANTHROPIC_DEFAULT_HAIKU_MODEL"]
                    modified = True
                if "ANTHROPIC_DEFAULT_SONNET_MODEL" in local_settings["env"]:
                    del local_settings["env"]["ANTHROPIC_DEFAULT_SONNET_MODEL"]
                    modified = True
                if "ANTHROPIC_DEFAULT_OPUS_MODEL" in local_settings["env"]:
                    # Change from GLM model to Opus model
                    if local_settings["env"]["ANTHROPIC_DEFAULT_OPUS_MODEL"] != DEFAULT_MODEL:
                        local_settings["env"]["ANTHROPIC_DEFAULT_OPUS_MODEL"] = DEFAULT_MODEL
                        modified = True
                
                # Update API token (always update to ensure Opus token is used)
                if "ANTHROPIC_AUTH_TOKEN" in local_settings["env"]:
                    local_settings["env"]["ANTHROPIC_AUTH_TOKEN"] = api_key
                    modified = True
                else:
                    # Add Opus token if not present
                    local_settings["env"]["ANTHROPIC_AUTH_TOKEN"] = api_key
                    modified = True
                
                # If env section is now empty, remove it
                if not local_settings["env"]:
                    del local_settings["env"]
                    modified = True
            
            if modified:
                # Write back to local settings file
                with open(local_settings_path, "w", encoding="utf-8") as f:
                    json.dump(local_settings, f, indent=2, ensure_ascii=False)
                
                print(f"[OK] Project-level GLM settings removed from: {local_settings_path.relative_to(project_root)}")
            else:
                print(f"[INFO] Project-level settings already configured for Opus")
        
        print()
        print("Configured environment variables:")
        print(f"   - ANTHROPIC_AUTH_TOKEN: {api_key[:20]}...")
        print(f"   - ANTHROPIC_DEFAULT_OPUS_MODEL: {DEFAULT_MODEL}")
        print()
        print("[OK] Claude Opus configuration complete!")
        print("Note: Restart Claude Code to load the new configuration automatically.")
        
        return True
    
    except json.JSONDecodeError as e:
        print(f"[ERROR] Invalid JSON in settings file")
        print(f"   Details: {e}")
        return False
    
    except Exception as e:
        print(f"[ERROR] Error during Opus configuration: {e}")
        return False


def main() -> None:
    """Main entry point"""
    # Get API key from command line argument or use default
    if len(sys.argv) >= 2:
        api_key = sys.argv[1]
    else:
        api_key = DEFAULT_API_KEY
        print(f"[OK] Using default Anthropic API key")
    
    # Get project root from command line (optional)
    project_root = None
    if len(sys.argv) >= 3:
        project_root = Path(sys.argv[2])
    
    # Validate key (basic check)
    if not api_key or len(api_key) < 10:
        print("❌ Error: API key appears to be invalid (too short)")
        sys.exit(1)
    
    success = setup_opus(api_key, project_root)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
