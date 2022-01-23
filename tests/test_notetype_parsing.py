import json
import unittest
from collections import defaultdict

from src.anking_notetypes.config_window import ntss_for_model
from src.anking_notetypes.notetype_setting_definitions import (
    anking_notetype_model,
    anking_notetype_names,
)


class TestNotetypeSettingParsing(unittest.TestCase):
    def test_nts_parsing(self):
        current = defaultdict(dict)
        for notetype_name, model in (
            (name, anking_notetype_model(name)) for name in anking_notetype_names()
        ):
            ntss = ntss_for_model(model)
            for nts in ntss:
                setting_name = nts.config["name"]
                setting_value = nts.setting_value(model)
                current[notetype_name][setting_name] = setting_value

        # with open("tests/settings.json", 'w') as f:
        #     json.dump(current, f)

        with open("tests/settings.json", "r") as f:
            expected = json.load(f)

        assert current == expected
