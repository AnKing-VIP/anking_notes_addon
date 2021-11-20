import json

from src.anking_notetypes.model_settings import (
    general_settings,
    setting_configs,
    settings_by_notetype,
)

conf = {
    notetype: {name: setting_configs[name]["default"] for name in setting_names}
    for notetype, setting_names in settings_by_notetype.items()
}

general = {name: setting_configs[name]["default"] for name in general_settings}

conf["general"] = general


with open("src/anking_notetypes/config.json", "w") as f:
    json.dump(conf, f)
