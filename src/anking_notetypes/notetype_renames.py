import re
from typing import Dict, List


# Add note type renames here as "old bundled name": "new bundled name".
# The old name is still used to find existing note types in users' collections.
NOTETYPE_RENAMES: Dict[str, str] = {
    "AnKingMCAT": "AnKing MCAT",
}


def canonical_notetype_name(notetype_name: str) -> str:
    return NOTETYPE_RENAMES.get(notetype_name, notetype_name)


def legacy_notetype_names(canonical_name: str) -> List[str]:
    return [
        old_name
        for old_name, new_name in NOTETYPE_RENAMES.items()
        if new_name == canonical_name
    ]


def matching_notetype_names(canonical_name: str) -> List[str]:
    return [canonical_name, *legacy_notetype_names(canonical_name)]


def renamed_notetype_name(model_name: str) -> str:
    # Match bare name or copy-suffixed form only. AnkiHub-qualified forms
    # like "AnKingMCAT (AnKing-MCAT / AnKingMed)" are owned by the AnkiHub
    # add-on — we don't rename them here because the deck portion may or
    # may not be renamed upstream, and we can't know.
    for old_name, new_name in NOTETYPE_RENAMES.items():
        match = re.match(rf"({re.escape(old_name)})(?=$|-)", model_name)
        if match:
            return new_name + model_name[match.end() :]
    return model_name
