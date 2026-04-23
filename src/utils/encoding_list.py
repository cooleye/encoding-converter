from typing import List, Tuple
import platform

def _get_ansi_encoding():
    """根据操作系统返回 ANSI 编码"""
    if platform.system() == 'Windows':
        return ('ANSI (系统默认)', 'mbcs')
    else:
        return ('ANSI (CP1252)', 'cp1252')

ENCODING_GROUPS = [
    ("Unicode", [
        ("UTF-8", "utf-8"),
        ("UTF-8 (with BOM)", "utf-8-sig"),
        ("UTF-16 LE", "utf-16-le"),
        ("UTF-16 BE", "utf-16-be"),
        ("UTF-32 LE", "utf-32-le"),
        ("UTF-32 BE", "utf-32-be"),
    ]),
    ("Chinese", [
        ("GBK", "gbk"),
        ("GB2312", "gb2312"),
        ("GB18030", "gb18030"),
        ("Big5", "big5"),
        ("Big5-HKSCS", "big5hkscs"),
    ]),
    ("Japanese", [
        ("Shift-JIS", "shift_jis"),
        ("EUC-JP", "euc_jp"),
        ("ISO-2022-JP", "iso2022_jp"),
        ("CP932", "cp932"),
    ]),
    ("Korean", [
        ("EUC-KR", "euc_kr"),
        ("CP949", "cp949"),
        ("ISO-2022-KR", "iso2022_kr"),
    ]),
    ("Western European", [
        _get_ansi_encoding(),
        ("ISO-8859-1 (Latin-1)", "iso-8859-1"),
        ("ISO-8859-15 (Latin-9)", "iso-8859-15"),
        ("Windows-1252", "cp1252"),
        ("ASCII", "ascii"),
        ("Mac Roman", "mac_roman"),
    ]),
    ("Cyrillic", [
        ("KOI8-R", "koi8_r"),
        ("KOI8-U", "koi8_u"),
        ("Windows-1251", "cp1251"),
        ("ISO-8859-5", "iso-8859-5"),
    ]),
    ("Arabic", [
        ("Windows-1256", "cp1256"),
        ("ISO-8859-6", "iso-8859-6"),
    ]),
    ("Greek", [
        ("Windows-1253", "cp1253"),
        ("ISO-8859-7", "iso-8859-7"),
    ]),
    ("Hebrew", [
        ("Windows-1255", "cp1255"),
        ("ISO-8859-8", "iso-8859-8"),
    ]),
    ("Other", [
        ("ISO-8859-2 (Central European)", "iso-8859-2"),
        ("ISO-8859-3 (South European)", "iso-8859-3"),
        ("ISO-8859-4 (North European)", "iso-8859-4"),
        ("Windows-1250 (Central European)", "cp1250"),
        ("Windows-1254 (Turkish)", "cp1254"),
        ("Windows-1257 (Baltic)", "cp1257"),
        ("Windows-1258 (Vietnamese)", "cp1258"),
        ("TIS-620 (Thai)", "tis_620"),
    ]),
]


def get_all_encodings():
    # type: () -> List[Tuple[str, str]]
    result = []
    for _, encodings in ENCODING_GROUPS:
        result.extend(encodings)
    return result


def get_display_name(codec_name):
    # type: (str) -> str
    for _, encodings in ENCODING_GROUPS:
        for display, codec in encodings:
            if codec == codec_name:
                return display
    return codec_name


def get_codec_name(display_name):
    # type: (str) -> Optional[str]
    for _, encodings in ENCODING_GROUPS:
        for display, codec in encodings:
            if display == display_name:
                return codec
    return None
