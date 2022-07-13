import re
from concurrent.futures import Future
from copy import deepcopy
from typing import Dict, List

from aqt import mw
from aqt.utils import askUser, tooltip

from ..constants import NOTETYPE_COPY_RE
from ..notetype_setting_definitions import anking_notetype_names
from ..utils import adjust_field_ords, create_backup


def handle_extra_notetype_versions():

    # mids of copies of the AnKing notetype identified by its name
    copy_mids_by_notetype: Dict[str, List[int]] = dict()
    for notetype_name in anking_notetype_names():

        if mw.col.models.by_name(notetype_name) is None:
            continue

        notetype_copy_mids = [
            x.id
            for x in mw.col.models.all_names_and_ids()
            if re.match(NOTETYPE_COPY_RE.format(notetype_name=notetype_name), x.name)
        ]
        if notetype_copy_mids:
            copy_mids_by_notetype[notetype_name] = notetype_copy_mids

    if not copy_mids_by_notetype:
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
        on_done=lambda future: convert(future, copy_mids_by_notetype),
        label="Creating Backup...",
        immediate=True,
    )


def convert(future: Future, copy_mids_by_notetype: Dict[str, List[int]] = dict()):

    future.result()  # throws an exception if there was an exception in the background task

    for notetype_name, copy_mids in copy_mids_by_notetype.items():
        notetype = mw.col.models.by_name(notetype_name)
        for copy_mid in copy_mids:
            notetype_copy = mw.col.models.get(copy_mid)  # type: ignore

            # First change the <notetype_copy> to be exactly like <notetype> to then be able to
            # change the note type of notes of type <notetype_copy> without problems
            new_notetype = deepcopy(notetype)
            new_notetype["id"] = notetype_copy["id"]
            new_notetype["name"] = notetype_copy["name"]  # to prevent duplicates
            new_notetype["usn"] = -1  # triggers full sync

            # XXX TODO: check if fields would be deleted by this and warn the user?
            # XXX TODO: check if this is reliable
            new_notetype = adjust_field_ords(notetype_copy, new_notetype)

            mw.col.models.update_dict(new_notetype)

            # change the notes of type <notetype_copy> to type <notetype>
            nids_with_notetype_copy_type = mw.col.find_notes(
                f'"note:{notetype_copy["name"]}"'
            )
            mw.col.models.change(
                notetype_copy,
                nids_with_notetype_copy_type,  # type: ignore
                notetype,
                {i: i for i in range(len(notetype["flds"]))},
                None,
            )

            # remove the notetype copy
            mw.col.models.remove(copy_mid)  # type: ignore

    mw.reset()
    tooltip("Note types were converted successfully.")
