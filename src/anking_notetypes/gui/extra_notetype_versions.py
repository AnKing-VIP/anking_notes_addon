from concurrent.futures import Future
from copy import deepcopy
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple

from aqt import mw
from aqt.utils import askUser, tooltip

from ..notetype_renames import legacy_notetype_names, matching_notetype_names
from ..notetype_setting_definitions import anking_notetype_names, is_notetype_copy
from ..utils import adjust_fields, create_backup

if TYPE_CHECKING:
    from anki.models import NotetypeDict


def handle_extra_notetype_versions() -> None:
    # mids of copies of the AnKing notetype, keyed by canonical base name
    copy_mids_by_notetype_base_name: Dict[str, List[int]] = dict()
    # (legacy_name, canonical_name) pairs for mains that will be renamed during conversion
    legacy_mains_to_rename: List[Tuple[str, str]] = []
    for notetype_base_name in anking_notetype_names():
        matching_names = matching_notetype_names(notetype_base_name)
        if _first_existing_notetype_name(matching_names) is None:
            continue

        notetype_copy_mids = [
            x.id
            for x in mw.col.models.all_names_and_ids()
            for matching_name in matching_names
            if is_notetype_copy(x.name, matching_name)
        ]
        if not notetype_copy_mids:
            continue

        copy_mids_by_notetype_base_name[notetype_base_name] = notetype_copy_mids
        if mw.col.models.by_name(notetype_base_name) is None:
            for legacy_name in legacy_notetype_names(notetype_base_name):
                if mw.col.models.by_name(legacy_name) is not None:
                    legacy_mains_to_rename.append((legacy_name, notetype_base_name))
                    break

    if not copy_mids_by_notetype_base_name:
        return

    if not askUser(
        _build_confirmation_message(legacy_mains_to_rename),
        title="Extra copies of AnKing note types",
    ):
        return

    mw.taskman.with_progress(
        create_backup,
        on_done=lambda future: convert_extra_notetypes(
            future, copy_mids_by_notetype_base_name
        ),
        label="Creating Backup...",
        immediate=True,
    )


def convert_extra_notetypes(
    future: Future, copy_mids_by_notetype_base_name: Dict[str, List[int]]
) -> None:
    """
    Change note type of notes that have copies of an AnKing note type as a type to the original note type.
    Remove the extra note type copies.
    """

    future.result()  # throws an exception if there was an exception in the background task

    for notetype_base_name, copy_mids in copy_mids_by_notetype_base_name.items():
        model = mw.col.models.by_name(notetype_base_name)
        if model is None:
            # Only a legacy-named main exists — rename it to canonical so
            # copies (including canonical-named copies) fold into the new name.
            model = _rename_legacy_main_to_canonical(notetype_base_name)
        for copy_mid in copy_mids:
            model_copy = mw.col.models.get(copy_mid)  # type: ignore

            # First change the <notetype_copy> to be exactly like <notetype> to then be able to
            # change the note type of notes of type <notetype_copy> without problems
            new_model = deepcopy(model)
            new_model["id"] = model_copy["id"]
            new_model["name"] = model_copy["name"]  # to prevent duplicates
            new_model["usn"] = -1  # triggers full sync
            new_model["flds"] = adjust_fields(model_copy["flds"], new_model["flds"])
            mw.col.models.update_dict(new_model)

            # change the notes of type <notetype_copy> to type <notetype>
            nids_with_notetype_copy_type = mw.col.find_notes(
                f'"note:{model_copy["name"]}"'
            )
            mw.col.models.change(
                model_copy,
                nids_with_notetype_copy_type,  # type: ignore
                model,
                {i: i for i in range(len(model["flds"]))},
                None,
            )

            # remove the notetype copy
            mw.col.models.remove(copy_mid)  # type: ignore

    mw.reset()
    tooltip("Note types were converted successfully.")


def _build_confirmation_message(
    legacy_mains_to_rename: List[Tuple[str, str]],
) -> str:
    message = (
        "There are extra copies of AnKing note types. Do you want to convert all "
        "note types with names like "
        'for example "AnKingOverhaul-1dgs0" to "AnKingOverhaul" respectively?\n\n'
        "This will delete the extra note types and require a full upload of the "
        "collection the next time you sync with AnkiWeb. A backup will be created "
        "before the changes are applied.\n\n"
    )
    if legacy_mains_to_rename:
        renames = "\n".join(
            f'  - "{legacy}" → "{canonical}"'
            for legacy, canonical in legacy_mains_to_rename
        )
        message += (
            "The following note types will also be renamed to their current "
            f"names:\n{renames}\n\n"
        )
    message += (
        "No matter what you chose the AnKing Note Types window will open after "
        "you select an option."
    )
    return message


def _first_existing_notetype_name(notetype_names: List[str]) -> Optional[str]:
    return next(
        (
            notetype_name
            for notetype_name in notetype_names
            if mw.col.models.by_name(notetype_name) is not None
        ),
        None,
    )


def _rename_legacy_main_to_canonical(canonical_name: str) -> Optional["NotetypeDict"]:
    for legacy_name in legacy_notetype_names(canonical_name):
        legacy_model = mw.col.models.by_name(legacy_name)
        if legacy_model is None:
            continue
        legacy_model["name"] = canonical_name
        legacy_model["usn"] = -1
        mw.col.models.update_dict(legacy_model)
        return mw.col.models.by_name(canonical_name)
    return None
