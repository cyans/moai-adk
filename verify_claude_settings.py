import json
import os

settings_path = r"C:\Users\cyan9\.claude\settings.json"

def verify_settings():
    try:
        with open(settings_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        env = data.get('env', {})
        print("Current env settings:")
        print(json.dumps(env, indent=2))
        
        expected_keys = [
            "ANTHROPIC_AUTH_TOKEN",
            "ANTHROPIC_BASE_URL",
            "ANTHROPIC_DEFAULT_HAIKU_MODEL",
            "ANTHROPIC_DEFAULT_SONNET_MODEL",
            "ANTHROPIC_DEFAULT_OPUS_MODEL"
        ]
        
        missing = [k for k in expected_keys if k not in env]
        if missing:
            print(f"MISSING KEYS: {missing}")
        else:
            print("All expected keys present.")

    except Exception as e:
        print(f"Error reading file: {e}")

if __name__ == "__main__":
    verify_settings()
