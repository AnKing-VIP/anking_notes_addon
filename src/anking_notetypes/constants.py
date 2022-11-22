NOTETYPE_COPY_RE = r"{notetype_name}-[a-zA-Z0-9]{{5}}"
ANKIHUB_NOTETYPE_RE = r"{notetype_name} \(.+ / .+\)"

# has to be the same as in the ankihub addon
ANKIHUB_NOTE_TYPE_MODIFICATION_STRING = "ANKIHUB MODFICATIONS"
ANKIHUB_TEMPLATE_SNIPPET_RE = (
    f"<!-- BEGIN {ANKIHUB_NOTE_TYPE_MODIFICATION_STRING} -->"
    r"[\w\W]*"
    f"<!-- END {ANKIHUB_NOTE_TYPE_MODIFICATION_STRING} -->"
)
