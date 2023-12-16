import re
import time

from aqt import mw

from .constants import ANKIHUB_TEMPLATE_END_COMMENT, ANKIHUB_TEMPLATE_SNIPPET_RE
from .notetype_setting_definitions import anking_notetype_model

try:
    from anki.models import NotetypeDict  # type: ignore # pylint: disable=unused-import
except:
    pass


def update_notetype_to_newest_version(
    notetype: "NotetypeDict", notetype_base_name: str
) -> None:
    new_notetype = anking_notetype_model(notetype_base_name)
    new_notetype["id"] = notetype["id"]
    new_notetype["name"] = notetype["name"]  # keep the name
    new_notetype["mod"] = int(time.time())  # not sure if this is needed
    new_notetype["usn"] = -1  # triggers full sync

    # retain the ankihub_id field if it exists on the old model
    ankihub_field = next(
        (x for x in notetype["flds"] if x["name"] == "ankihub_id"), None
    )
    if ankihub_field:
        new_notetype["flds"].append(ankihub_field)

    new_notetype = adjust_field_ords(notetype, new_notetype)

    # the order is important here
    # the end comment must be added after the ankihub snippet
    retain_ankihub_modifications_to_templates(notetype, new_notetype)
    retain_content_below_ankihub_end_comment_or_add_end_comment(notetype, new_notetype)

    notetype.update(new_notetype)


def retain_ankihub_modifications_to_templates(
    old_notetype: "NotetypeDict", new_notetype: "NotetypeDict"
) -> "NotetypeDict":
    for old_template, new_template in zip(old_notetype["tmpls"], new_notetype["tmpls"]):
        for template_type in ["qfmt", "afmt"]:
            m = re.search(ANKIHUB_TEMPLATE_SNIPPET_RE, old_template[template_type])
            if not m:
                continue

            new_template[template_type] = (
                new_template[template_type].rstrip("\n ") + "\n\n" + m.group(0)
            )

    return new_notetype


def retain_content_below_ankihub_end_comment_or_add_end_comment(
    old_notetype: "NotetypeDict", new_notetype: "NotetypeDict"
) -> "NotetypeDict":
    # will add the end comment if it doesn't exist
    for old_template, new_template in zip(old_notetype["tmpls"], new_notetype["tmpls"]):
        for template_type in ["qfmt", "afmt"]:
            m = re.search(
                rf"{ANKIHUB_TEMPLATE_END_COMMENT}[\w\W]*",
                old_template[template_type],
            )
            if m:
                new_template[template_type] = (
                    new_template[template_type].rstrip("\n ") + "\n\n" + m.group(0)
                )
            else:
                new_template[template_type] = (
                    new_template[template_type].rstrip("\n ")
                    + "\n\n"
                    + ANKIHUB_TEMPLATE_END_COMMENT
                    + "\n\n"
                )

    return new_notetype


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
