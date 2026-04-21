# pylint: disable=protected-access
from unittest.mock import MagicMock, patch

import pytest

from src.anking_notetypes import notetype_setting_definitions, utils
from src.anking_notetypes.notetype_renames import (
    NOTETYPE_RENAMES,
    canonical_notetype_name,
    matching_notetype_names,
    renamed_notetype_name,
)
from src.anking_notetypes.notetype_setting import order_names
from src.anking_notetypes.notetype_setting_definitions import notetype_base_name

FAKE_RENAMES = {"Old-AnKing": "AnKingOverhaul"}


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
        with patch.dict(NOTETYPE_RENAMES, FAKE_RENAMES):
            assert canonical_notetype_name("Old-AnKing") == "AnKingOverhaul"
            assert canonical_notetype_name("AnKingOverhaul") == "AnKingOverhaul"

    def test_matching_notetype_names(self):
        with patch.dict(NOTETYPE_RENAMES, FAKE_RENAMES):
            assert matching_notetype_names("AnKingOverhaul") == [
                "AnKingOverhaul",
                "Old-AnKing",
            ]

    def test_renamed_notetype_name(self):
        with patch.dict(NOTETYPE_RENAMES, FAKE_RENAMES):
            assert renamed_notetype_name("Old-AnKing") == "AnKingOverhaul"
            assert renamed_notetype_name("Old-AnKing-1dgs0") == "AnKingOverhaul-1dgs0"
            assert (
                renamed_notetype_name("Old-AnKing (AnKing / Example)")
                == "AnKingOverhaul (AnKing / Example)"
            )

    def test_notetype_base_name_recognizes_legacy_name(self):
        with patch.dict(NOTETYPE_RENAMES, FAKE_RENAMES):
            assert notetype_base_name("Old-AnKing") == "AnKingOverhaul"
            assert notetype_base_name("Old-AnKing-1dgs0") == "AnKingOverhaul"


@pytest.fixture
def notetypes_path(tmp_path):
    with patch.object(
        notetype_setting_definitions, "ANKING_NOTETYPES_PATH", tmp_path
    ), patch.dict(NOTETYPE_RENAMES, FAKE_RENAMES):
        yield tmp_path


class TestNotetypeFolderName:
    def test_prefers_canonical_folder_when_present(self, notetypes_path):
        (notetypes_path / "AnKingOverhaul").mkdir()
        (notetypes_path / "Old-AnKing").mkdir()

        assert (
            notetype_setting_definitions._notetype_folder_name("AnKingOverhaul")
            == "AnKingOverhaul"
        )

    def test_falls_back_to_legacy_folder(self, notetypes_path):
        (notetypes_path / "Old-AnKing").mkdir()

        assert (
            notetype_setting_definitions._notetype_folder_name("AnKingOverhaul")
            == "Old-AnKing"
        )

    def test_returns_canonical_when_no_folder_exists(
        self, notetypes_path  # pylint: disable=unused-argument
    ):
        assert (
            notetype_setting_definitions._notetype_folder_name("AnKingOverhaul")
            == "AnKingOverhaul"
        )


class TestUpdatedNotetypeName:
    def test_returns_unchanged_when_no_rename_applies(self):
        with patch.dict(NOTETYPE_RENAMES, {}, clear=True):
            assert utils._updated_notetype_name("Unrelated") == "Unrelated"

    def test_renames_when_new_name_not_in_collection(self):
        mw_mock = MagicMock()
        mw_mock.col.models.by_name.return_value = None

        with patch.object(utils, "mw", mw_mock), patch.dict(
            NOTETYPE_RENAMES, FAKE_RENAMES
        ):
            assert utils._updated_notetype_name("Old-AnKing") == "AnKingOverhaul"

    def test_keeps_old_name_when_new_name_already_exists(self):
        mw_mock = MagicMock()
        mw_mock.col.models.by_name.return_value = {"id": 1, "name": "AnKingOverhaul"}

        with patch.object(utils, "mw", mw_mock), patch.dict(
            NOTETYPE_RENAMES, FAKE_RENAMES
        ):
            assert utils._updated_notetype_name("Old-AnKing") == "Old-AnKing"
