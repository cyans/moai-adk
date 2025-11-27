import json
import os

settings_path = r"C:\Users\cyan9\.claude\settings.json"

new_env_settings = {
    "ANTHROPIC_AUTH_TOKEN": "9b321e59aaa04c778dc551135f0befec.MOAYLe5nctGn1dPO",
    "ANTHROPIC_BASE_URL": "https://api.z.ai/api/anthropic",
    "ANTHROPIC_DEFAULT_HAIKU_MODEL": "glm-4.5-air",
    "ANTHROPIC_DEFAULT_SONNET_MODEL": "glm-4.6",
    "ANTHROPIC_DEFAULT_OPUS_MODEL": "glm-4.6"
}

def update_settings():
    if not os.path.exists(settings_path):
        print(f"File not found: {settings_path}")
        # Create it if it doesn't exist? The user said "put this in there".
        # Let's assume we should create it or just fail if directory missing.
        # But usually .claude dir exists.
        try:
            os.makedirs(os.path.dirname(settings_path), exist_ok=True)
            data = {}
        except Exception as e:
            print(f"Error creating directory: {e}")
            return
    else:
        try:
            with open(settings_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except json.JSONDecodeError:
            print("Error decoding JSON, starting with empty object")
            data = {}
        except Exception as e:
            print(f"Error reading file: {e}")
            return

    # Update env
    data['env'] = new_env_settings

    try:
        with open(settings_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        print(f"Successfully updated {settings_path}")
    except Exception as e:
        print(f"Error writing file: {e}")

if __name__ == "__main__":
    update_settings()
