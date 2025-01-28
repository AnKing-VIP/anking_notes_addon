import re
import time
from copy import deepcopy

from aqt import mw

from .constants import (
    ANKIHUB_CSS_END_COMMENT,
    ANKIHUB_CSS_END_COMMENT_RE,
    ANKIHUB_HTML_END_COMMENT,
    ANKIHUB_HTML_END_COMMENT_RE,
    ANKIHUB_TEMPLATE_SNIPPET_RE,
)
from .notetype_setting_definitions import anking_notetype_model

try:
    from anki.models import NotetypeDict  # type: ignore # pylint: disable=unused-import
except:
    pass


def update_notetype_to_newest_version(
    model: "NotetypeDict", notetype_base_name: str
) -> None:
    new_model = anking_notetype_model(notetype_base_name)
    new_model["id"] = model["id"]
    new_model["name"] = model["name"]  # keep the name
    new_model["mod"] = int(time.time())  # not sure if this is needed
    new_model["usn"] = -1  # triggers full sync

    # retain the ankihub_id field if it exists on the old model
    ankihub_field = next((x for x in model["flds"] if x["name"] == "ankihub_id"), None)
    if ankihub_field:
        new_model["flds"].append(ankihub_field)

    new_model = adjust_field_ords(model, new_model)

    new_model = _retain_content_below_ankihub_end_comment_or_add_end_comment(
        model, new_model
    )

    model.update(new_model)


def _retain_content_below_ankihub_end_comment_or_add_end_comment(
    old_model: "NotetypeDict", new_model: "NotetypeDict"
) -> "NotetypeDict":
    updated_templates = []
    for old_template, new_template in zip(old_model["tmpls"], new_model["tmpls"]):
        updated_template = deepcopy(new_template)
        for template_side in ["qfmt", "afmt"]:
            updated_template[template_side] = _updated_note_type_content(
                old_template[template_side],
                new_template[template_side],
                content_type="html",
            )
        updated_templates.append(updated_template)

    result = deepcopy(new_model)
    result["tmpls"] = updated_templates

    result["css"] = _updated_note_type_content(
        old_content=old_model["css"],
        new_content=new_model["css"],
        content_type="css",
    )

    return result


def _updated_note_type_content(
    old_content: str,
    new_content: str,
    content_type: str,
) -> str:
    """Returns updated content with preserved content below ankihub end comment.

    Args:
      old_content: Original content to preserve custom additions from
      new_content: New base content to use
      content_type: Either "html" or "css" to determine comment style
    """
    if content_type == "html":
        end_comment = ANKIHUB_HTML_END_COMMENT
        end_comment_pattern = ANKIHUB_HTML_END_COMMENT_RE
    else:
        end_comment = ANKIHUB_CSS_END_COMMENT
        end_comment_pattern = ANKIHUB_CSS_END_COMMENT_RE

    snippet_match = re.search(ANKIHUB_TEMPLATE_SNIPPET_RE, old_content)
    snippet_to_migrate = snippet_match.group() if snippet_match else ""

    text_to_migrate_match = re.search(end_comment_pattern, old_content)
    text_to_migrate = (
        text_to_migrate_match.group("text_to_migrate") if text_to_migrate_match else ""
    )

    # Remove end comment and content below it.
    # It will be added back below.
    result = re.sub(end_comment_pattern, "", new_content)

    return (
        result.rstrip("\n ")
        + (f"\n{snippet_to_migrate}" if snippet_to_migrate else "")
        + "\n\n"
        + end_comment
        + "\n"
        + text_to_migrate.strip("\n ")
    )


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
