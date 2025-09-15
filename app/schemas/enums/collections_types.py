from enum import Enum

class CollectionType(str, Enum):
    MIXED = "mixed"
    TASKS_ONLY = "tasks-only"
    NOTES_ONLY = "notes-only"

