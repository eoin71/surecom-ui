"""
Bootstrap Icons -> Heroicons name map, used when migrating RAMS_generator's
templates. Kept as data so the substitution is auditable rather than ad hoc.

Entries with a note are approximations: Heroicons is a smaller set than
Bootstrap Icons and has no direct counterpart.
"""

BOOTSTRAP_TO_HEROICON = {
    "arrow-clockwise": "arrow-path",
    "arrow-left": "arrow-left",
    "box-arrow-in-right": "arrow-right-end-on-rectangle",
    "box-arrow-right": "arrow-right-start-on-rectangle",
    "briefcase": "briefcase",
    "building": "building-office",  # Bootstrap's generic building
    "calendar": "calendar",
    "check-circle": "check-circle",
    "check-lg": "check",
    "check-square": "check-circle",  # no checkbox glyph; circle instead of square
    "chevron-down": "chevron-down",
    "clipboard": "clipboard",
    "download": "arrow-down-tray",
    "envelope": "envelope",
    "exclamation-triangle": "exclamation-triangle",
    "eye": "eye",
    "file-earmark": "document",
    "file-earmark-pdf": "document-text",  # loses the PDF format cue
    "file-earmark-plus": "document-plus",
    "file-earmark-word": "document-text",  # loses the Word format cue; same glyph as PDF
    "file-earmark-x": "document-minus",  # 'remove document' rather than 'invalid file'
    "file-text": "document-text",
    "files": "document-duplicate",
    "folder": "folder",
    "gear": "cog-6-tooth",
    "gear-fill": "cog-6-tooth",  # solid variant unavailable; outline only
    "geo-alt": "map-pin",
    "hospital": "building-office-2",  # no hospital icon in Heroicons
    "hourglass-split": "clock",  # no hourglass; reads as 'time' not 'in progress'
    "house": "home",
    "inbox": "inbox",
    "info-circle": "information-circle",
    "lightbulb": "light-bulb",
    "list": "bars-3",
    "list-check": "clipboard-document-check",  # heavier glyph than a checked list
    "list-task": "list-bullet",
    "list-ul": "list-bullet",
    "lock": "lock-closed",
    "lock-fill": "lock-closed",  # solid variant unavailable; outline only
    "pencil": "pencil-square",
    "people-fill": "users",
    "person-badge": "identification",
    "person-circle": "user-circle",
    "person-plus": "user-plus",
    "plus-circle": "plus-circle",
    "question-circle": "question-mark-circle",
    "save": "document-arrow-down",  # no floppy/save glyph
    "search": "magnifying-glass",
    "shield-check": "shield-check",
    "sliders": "adjustments-horizontal",
    "trash": "trash",
    "warning": "exclamation-triangle",  # same glyph as exclamation-triangle
    "x-lg": "x-mark",
}
