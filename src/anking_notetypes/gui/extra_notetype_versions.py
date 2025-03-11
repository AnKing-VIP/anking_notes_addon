import re
from concurrent.futures import Future
from copy import deepcopy
from typing import Dict, List

from aqt import mw
from aqt.utils import askUser, tooltip

from ..constants import NOTETYPE_COPY_RE
from ..notetype_setting_definitions import anking_notetype_names
from ..utils import adjust_fields, create_backup


def handle_extra_notetype_versions() -> None:
    # mids of copies of the AnKing notetype identified by its name
    copy_mids_by_notetype_base_name: Dict[str, List[int]] = dict()
    for notetype_base_name in anking_notetype_names():
        if mw.col.models.by_name(notetype_base_name) is None:
            continue

        notetype_copy_mids = [
            x.id
            for x in mw.col.models.all_names_and_ids()
            if re.match(
                NOTETYPE_COPY_RE.format(notetype_base_name=notetype_base_name), x.name
            )
        ]
        if notetype_copy_mids:
            copy_mids_by_notetype_base_name[notetype_base_name] = notetype_copy_mids

    if not copy_mids_by_notetype_base_name:
        return

    if not askUser(
        "There are extra copies of AnKing note types. Do you want to convert all note types with names like "
        'for example "AnKingOverhaul-1dgs0" to "AnKingOverhaul" respectively?\n\n'
        "This will delete the extra note types and require a full upload of the collection "
        "the next time you sync with AnkiWeb. A backup will be created before the changes are applied.\n\n"
        "No matter what you chose the AnKing Note Types window will open after you select an option.",
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
