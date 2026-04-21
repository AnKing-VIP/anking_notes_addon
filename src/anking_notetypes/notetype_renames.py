import re
from typing import Dict, List


# Add note type renames here as "old bundled name": "new bundled name".
# The old name is still used to find existing note types in users' collections.
NOTETYPE_RENAMES: Dict[str, str] = {
    "AnKingMCAT": "AnKing MCAT",
}

# Full renames for AnkiHub-qualified names where the deck portion also changed
# and cannot be derived from NOTETYPE_RENAMES alone.
FULL_NOTETYPE_RENAMES: Dict[str, str] = {
    "AnKingMCAT (AnKing-MCAT / AnKingMed)": (
        "AnKing MCAT (AnKing MCAT Deck / AnKingMed)"
    ),
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
    for old_full, new_full in FULL_NOTETYPE_RENAMES.items():
        match = re.match(rf"{re.escape(old_full)}(?=$|-)", model_name)
        if match:
            return new_full + model_name[match.end() :]

    for old_name, new_name in NOTETYPE_RENAMES.items():
        match = re.match(rf"({re.escape(old_name)})(?=$| |-)", model_name)
        if match:
            return new_name + model_name[match.end() :]
    return model_name
