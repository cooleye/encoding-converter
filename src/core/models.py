from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class FileStatus(Enum):
    PENDING = "pending"
    DETECTING = "detecting"
    READY = "ready"
    CONVERTING = "converting"
    COMPLETED = "completed"
    SKIPPED = "skipped"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ErrorStrategy(Enum):
    STRICT = "strict"
    IGNORE = "ignore"
    REPLACE = "replace"
    BACKSLASHREPLACE = "backslashreplace"
    SURROGATEESCAPE = "surrogateescape"


@dataclass
class FileEntry:
    path: str
    size: int
    detected_encoding: Optional[str] = None
    encoding_confidence: float = 0.0
    has_bom: bool = False
    bom_type: Optional[str] = None
    status: FileStatus = FileStatus.PENDING
    progress: int = 0
    status_text: str = ""
    error_message: Optional[str] = None


@dataclass
class ConversionConfig:
    source_encoding: str = ""
    target_encoding: str = "utf-8"
    auto_detect: bool = True
    keep_per_file_encoding: bool = False
    create_backup: bool = True
    strip_bom: bool = False
    add_bom: bool = False
    error_strategy: ErrorStrategy = ErrorStrategy.REPLACE
    max_lines_preview: int = 200


@dataclass
class ConversionResult:
    file_path: str
    success: bool
    source_encoding: str = ""
    target_encoding: str = ""
    backup_path: Optional[str] = None
    bytes_processed: int = 0
    error_message: Optional[str] = None
    skipped: bool = False
    skip_reason: str = ""
