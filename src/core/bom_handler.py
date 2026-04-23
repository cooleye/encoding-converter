from typing import Optional, Tuple

BOM_TABLE = [
    (b'\x00\x00\xfe\xff', 'utf-32-be', 4),
    (b'\xff\xfe\x00\x00', 'utf-32-le', 4),
    (b'\xfe\xff', 'utf-16-be', 2),
    (b'\xff\xfe', 'utf-16-le', 2),
    (b'\xef\xbb\xbf', 'utf-8-sig', 3),
]

ENCODING_BOM = {
    'utf-8-sig': b'\xef\xbb\xbf',
    'utf-8': b'\xef\xbb\xbf',
    'utf-16': b'\xff\xfe',
    'utf-16-le': b'\xff\xfe',
    'utf-16-be': b'\xfe\xff',
    'utf-32': b'\xff\xfe\x00\x00',
    'utf-32-le': b'\xff\xfe\x00\x00',
    'utf-32-be': b'\x00\x00\xfe\xff',
}


def detect_bom(file_path):
    # type: (str) -> Optional[Tuple[str, int]]
    try:
        with open(file_path, 'rb') as f:
            header = f.read(4)
    except (IOError, OSError):
        return None
    for marker, enc, length in BOM_TABLE:
        if header.startswith(marker):
            return (enc, length)
    return None


def strip_bom(content):
    # type: (bytes) -> Tuple[bytes, bool]
    for marker, _, length in BOM_TABLE:
        if content.startswith(marker):
            return (content[length:], True)
    return (content, False)


def get_bom_for_encoding(encoding):
    # type: (str) -> Optional[bytes]
    return ENCODING_BOM.get(encoding.lower())


def has_bom(file_path):
    # type: (str) -> bool
    return detect_bom(file_path) is not None
