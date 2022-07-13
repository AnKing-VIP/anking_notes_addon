import time

from aqt import mw

from .notetype_setting_definitions import anking_notetype_model

try:
    from anki.models import NotetypeDict  # type: ignore
except:
    pass


def update_notetype_to_newest_version(
    notetype: "NotetypeDict", notetype_archetype_name: str
):
    new_notetype = anking_notetype_model(notetype_archetype_name)
    new_notetype["id"] = notetype["id"]
    new_notetype["name"] = notetype["name"]  # keep the name
    new_notetype["mod"] = int(time.time())  # not sure if this is needed
    new_notetype["usn"] = -1  # triggers full sync
    new_notetype = adjust_field_ords(notetype, new_notetype)
    notetype.update(new_notetype)


def adjust_field_ords(
    cur_model: "NotetypeDict", new_model: "NotetypeDict"
) -> "NotetypeDict":
    # this makes sure that when fields get added or are moved
    # field contents end up in the field with the same name as before
    # note that the resulting model will have exactly the same set of fields as the new_model
    for fld in new_model["flds"]:
        if (
            cur_ord := next(
                (
                    _fld["ord"]
                    for _fld in cur_model["flds"]
                    if _fld["name"] == fld["name"]
                ),
                None,
            )
        ) is not None:
            fld["ord"] = cur_ord
        else:
            # it's okay to assign this to multiple fields because the
            # backend assigns new ords equal to the fields index
            fld["ord"] = len(new_model["flds"]) - 1
    return new_model


def create_backup() -> None:
    try:
        mw.col.create_backup(
            backup_folder=mw.pm.backupFolder(),
            force=True,
            wait_for_completion=True,
        )
    except AttributeError:  # < 2.1.50
        mw.col.close(downgrade=False)
        mw.backup()  # type: ignore
        mw.col.reopen(after_full_sync=False)
