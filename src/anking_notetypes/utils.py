import re
import time
from copy import deepcopy
from typing import Dict, List

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

    new_model["flds"] = adjust_fields(model["flds"], new_model["flds"])

    new_model = _retain_ankihub_modifications(model, new_model)

    model.update(new_model)


def _retain_ankihub_modifications(
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
    """Returns new_content with preserved ankihub modifications and
    preserved content below the ankihub end comment.

    Args:
      old_content: Original content to preserve ankihub modifications and custom additions from
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
    ankihub_snippet = snippet_match.group() if snippet_match else ""

    text_to_migrate_match = re.search(end_comment_pattern, old_content)
    text_to_migrate = (
        text_to_migrate_match.group("text_to_migrate") if text_to_migrate_match else ""
    )

    # Remove end comment and content below it.
    # It will be added back below.
    result = re.sub(end_comment_pattern, "", new_content)

    return (
        result.rstrip("\n ")
        + (f"\n{ankihub_snippet}" if ankihub_snippet else "")
        + "\n\n"
        + end_comment
        + "\n"
        + text_to_migrate.strip("\n ")
    )


def adjust_fields(
    cur_model_fields: List[Dict], new_model_fields: List[Dict]
) -> List[Dict]:
    """
    Prepares note type fields for updates by merging fields from the current and new models.

    This function handles several operations when updating note types:
    1. Maintains field content mapping by assigning appropriate 'ord' values to matching fields
    2. Assigns high 'ord' values to new fields so they start empty
    3. Appends fields that only exist locally to the new model
    4. Ensures the ankihub_id field remains at the end if it exists

    Returns:
        Updated note type fields
    """
    new_model_fields = deepcopy(new_model_fields)

    cur_model_field_map = {
        field["name"].lower(): field["ord"] for field in cur_model_fields
    }

    # Set appropriate ord values for each new field
    for new_model_field in new_model_fields:
        field_name_lower = new_model_field["name"].lower()
        if field_name_lower in cur_model_field_map:
            # If field exists in current model, preserve its ord value
            new_model_field["ord"] = cur_model_field_map[field_name_lower]
        else:
            # For new fields, set ord to a value outside the range of current fields
            new_model_field["ord"] = len(cur_model_fields) + 1

    # Append fields that only exist locally to the new model, while keeping the ankihub_id field at the end
    new_model_field_names = {field["name"].lower() for field in new_model_fields}
    only_local_fields = [
        field
        for field in cur_model_fields
        if field["name"].lower() not in new_model_field_names
    ]

    ankihub_id_field = next(
        (field for field in new_model_fields if field["name"] == "ankihub_id"), None
    )
    if ankihub_id_field:
        new_model_fields_without_ankihub = [
            field for field in new_model_fields if field["name"] != "ankihub_id"
        ]
        final_fields = (
            new_model_fields_without_ankihub + only_local_fields + [ankihub_id_field]
        )
    else:
        final_fields = new_model_fields + only_local_fields

    return final_fields


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
