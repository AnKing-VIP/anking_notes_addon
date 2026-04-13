from unittest.mock import patch

from src.anking_notetypes.notetype_setting import order_names
from src.anking_notetypes.notetype_renames import (
    NOTETYPE_RENAMES,
    canonical_notetype_name,
    matching_notetype_names,
    renamed_notetype_name,
)
from src.anking_notetypes.notetype_setting_definitions import notetype_base_name


class TestOrderNames:
    def test_basic(self):
        assert order_names(
            new_names=[
                "Lecture Notes",
                "First Aid",
                "Extra",
                "First Aid Links",
            ],
            current_names=[
                "Extra",
                "First Aid",
            ],
        ) == [
            "Extra",
            "First Aid",
            "Lecture Notes",
            "First Aid Links",
        ]

    def test_no_matches(self):
        assert order_names(
            new_names=["Apple", "Banana"], current_names=["Cherry", "Date"]
        ) == ["Apple", "Banana"]


class TestNotetypeRenames:
    def test_mcat_legacy_name_maps_to_new_name(self):
        assert canonical_notetype_name("AnKingMCAT") == "AnKing MCAT"
        assert notetype_base_name("AnKingMCAT") == "AnKing MCAT"
        assert (
            notetype_base_name("AnKingMCAT (AnKing-MCAT / AnKingMed)") == "AnKing MCAT"
        )
        assert (
            renamed_notetype_name("AnKingMCAT (AnKing-MCAT / AnKingMed)")
            == "AnKing MCAT (AnKing MCAT Deck / AnKingMed)"
        )

    def test_canonical_notetype_name(self):
        with patch.dict(NOTETYPE_RENAMES, {"Old-AnKing": "AnKingOverhaul"}):
            assert canonical_notetype_name("Old-AnKing") == "AnKingOverhaul"
            assert canonical_notetype_name("AnKingOverhaul") == "AnKingOverhaul"

    def test_matching_notetype_names(self):
        with patch.dict(NOTETYPE_RENAMES, {"Old-AnKing": "AnKingOverhaul"}):
            assert matching_notetype_names("AnKingOverhaul") == [
                "AnKingOverhaul",
                "Old-AnKing",
            ]

    def test_renamed_notetype_name(self):
        with patch.dict(NOTETYPE_RENAMES, {"Old-AnKing": "AnKingOverhaul"}):
            assert renamed_notetype_name("Old-AnKing") == "AnKingOverhaul"
            assert renamed_notetype_name("Old-AnKing-1dgs0") == "AnKingOverhaul-1dgs0"
            assert (
                renamed_notetype_name("Old-AnKing (AnKing / Example)")
                == "AnKingOverhaul (AnKing / Example)"
            )

    def test_notetype_base_name_recognizes_legacy_name(self):
        with patch.dict(NOTETYPE_RENAMES, {"Old-AnKing": "AnKingOverhaul"}):
            assert notetype_base_name("Old-AnKing") == "AnKingOverhaul"
            assert notetype_base_name("Old-AnKing-1dgs0") == "AnKingOverhaul"
