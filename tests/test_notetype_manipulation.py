import json
import unittest
from copy import deepcopy
from pathlib import Path

from src.anking_notetypes.gui.config_window import ntss_for_model
from src.anking_notetypes.notetype_setting import NotetypeSetting
from src.anking_notetypes.notetype_setting_definitions import (
    anking_notetype_model,
    anking_notetype_names,
)

try:
    from anki.models import NotetypeDict  # type: ignore
except:
    pass


class TestNotetypeSettingManipulation(unittest.TestCase):
    def test_notetype_manipulation(self):
        for notetype_name, model in (
            (name, anking_notetype_model(name)) for name in anking_notetype_names()
        ):
            ntss = ntss_for_model(model)
            conf = config(model)
            for nts in ntss:
                for test_value in test_values(nts, model):
                    temp_conf = deepcopy(conf)
                    temp_conf[nts.key(notetype_name)] = test_value
                    temp_model = deepcopy(model)
                    temp_model = nts.updated_model(
                        temp_model, temp_model["name"], temp_conf
                    )

                    d1 = config(temp_model)
                    d2 = temp_conf
                    if d1 != d2:
                        folder = Path(__file__).parent
                        with open(folder / "d1.json", "w") as f:
                            json.dump(d1, f)
                        with open(folder / "d2.json", "w") as f:
                            json.dump(d2, f)

                    self.assertDictEqual(
                        d1,
                        d2,
                        msg=f"{model['name']}.{nts.config['name']}",
                    )


def config(model: "NotetypeDict"):
    result = dict()
    ntss = ntss_for_model(model)
    for nts in ntss:
        setting_value = nts.setting_value(model)
        result[nts.key(model["name"])] = setting_value
    return result


def test_values(nts: "NotetypeSetting", model: "NotetypeDict"):
    config = nts.config
    if config["type"] == "checkbox":
        return [True, False]
    elif config["type"] == "re_checkbox":
        return [True, False]
    elif config["type"] == "wrap_checkbox":
        return [True, False]
    elif config["type"] == "text":
        return ["foo", "</div>"]
    elif config["type"] == "number":
        if config.get("decimal", False):
            return [1.0, 404.0]
        else:
            return [1, 404]
    elif config["type"] == "shortcut":
        return ["Ctrl + C", "asdf"]
    elif config["type"] == "dropdown":
        return config["options"]
    elif config["type"] == "color":
        return ["#D1CFCE", "black"]
    elif config["type"] == "font_family":
        return ["Arial Greek, Arial", "asdf"]
    elif config["type"] == "order":
        value = nts.setting_value(model)
        return [sorted(value), sorted(value, reverse=True)]
    else:
        assert False, "unknown type of notetype setting"
