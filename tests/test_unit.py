# pylint: disable=protected-access
from unittest.mock import MagicMock, patch

import pytest

from src.anking_notetypes import notetype_setting_definitions, utils
from src.anking_notetypes.gui import extra_notetype_versions
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

    def test_mcat_canonical_name_not_confused_with_anking_prefix(self):
        # "AnKing" is a valid base and prefix of "AnKing MCAT" — verify the
        # longer name wins so canonical MCAT names are not misclassified.
        assert notetype_base_name("AnKing MCAT") == "AnKing MCAT"
        assert notetype_base_name("AnKing MCAT-abcde") == "AnKing MCAT"
        assert (
            notetype_base_name("AnKing MCAT (AnKing MCAT Deck / AnKingMed)")
            == "AnKing MCAT"
        )

    def test_renamed_notetype_name_leaves_ankihub_qualified_alone(self):
        # AnkiHub-qualified notetypes are renamed by the AnkiHub add-on, not here.
        assert (
            renamed_notetype_name("AnKingMCAT (AnKing-MCAT / AnKingMed)")
            == "AnKingMCAT (AnKing-MCAT / AnKingMed)"
        )

    def test_renamed_notetype_name_ignores_unrelated_prefix(self):
        with patch.dict(NOTETYPE_RENAMES, FAKE_RENAMES):
            assert renamed_notetype_name("Old-AnKingology") == "Old-AnKingology"

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
            # AnkiHub-qualified form is left alone — AnkiHub owns that rename.
            assert (
                renamed_notetype_name("Old-AnKing (AnKing / Example)")
                == "Old-AnKing (AnKing / Example)"
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


class TestBuildConfirmationMessage:
    def test_no_legacy_mains_omits_rename_section(self):
        message = extra_notetype_versions._build_confirmation_message([])
        assert "renamed" not in message

    def test_lists_affected_legacy_mains(self):
        message = extra_notetype_versions._build_confirmation_message(
            [("AnKingMCAT", "AnKing MCAT"), ("Old-AnKing", "AnKingOverhaul")]
        )
        assert '"AnKingMCAT" → "AnKing MCAT"' in message
        assert '"Old-AnKing" → "AnKingOverhaul"' in message


class TestRenameLegacyMainToCanonical:
    def test_renames_legacy_main_and_returns_canonical_model(self):
        legacy_model = {"id": 42, "name": "Old-AnKing"}
        mw_mock = MagicMock()
        mw_mock.col.models.by_name.side_effect = lambda name: {
            "Old-AnKing": legacy_model,
        }.get(name)

        with patch.object(extra_notetype_versions, "mw", mw_mock), patch.dict(
            NOTETYPE_RENAMES, FAKE_RENAMES
        ):
            result = extra_notetype_versions._rename_legacy_main_to_canonical(
                "AnKingOverhaul"
            )

        assert legacy_model["name"] == "AnKingOverhaul"
        mw_mock.col.models.update_dict.assert_called_once_with(legacy_model)
        assert result is legacy_model

    def test_returns_none_when_no_legacy_main_exists(self):
        mw_mock = MagicMock()
        mw_mock.col.models.by_name.return_value = None

        with patch.object(extra_notetype_versions, "mw", mw_mock), patch.dict(
            NOTETYPE_RENAMES, FAKE_RENAMES
        ):
            assert (
                extra_notetype_versions._rename_legacy_main_to_canonical(
                    "AnKingOverhaul"
                )
                is None
            )
        mw_mock.col.models.update_dict.assert_not_called()
