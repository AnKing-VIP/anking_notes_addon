import json

from src.anking_notetypes.model_settings import setting_configs, settings_by_notetype

d = {
    notetype : {
        name : setting_configs[name]["default"]
        for name in setting_names
    }
    for notetype, setting_names in settings_by_notetype.items()
}

with open("src/anking_notetypes/config.json", "w") as f:
    json.dump(d, f)
