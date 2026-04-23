import os
from typing import Optional, Tuple

import charset_normalizer
from chardet import UniversalDetector

SAMPLE_SIZE = 128 * 1024
CONFIDENCE_THRESHOLD = 0.7


class EncodingDetector(object):

    def detect(self, file_path):
        # type: (str) -> Tuple[str, float]
        sample = self._read_sample(file_path)
        if not sample:
            return ("ascii", 1.0)

        bom_encoding = self._detect_bom(sample)
        if bom_encoding:
            return (bom_encoding, 1.0)

        result = charset_normalizer.detect(sample)
        if result and result.get("encoding") and result.get("confidence", 0) >= CONFIDENCE_THRESHOLD:
            enc = result["encoding"].lower()
            enc = self._normalize_cjk_detection(enc, sample)
            return (enc, result["confidence"])

        detector = UniversalDetector()
        detector.feed(sample)
        detector.close()
        chardet_result = detector.result
        if chardet_result and chardet_result.get("encoding"):
            enc = chardet_result["encoding"].lower()
            conf = chardet_result.get("confidence", 0.0)
            if conf >= CONFIDENCE_THRESHOLD:
                return (enc, conf)

        if result and result.get("encoding"):
            enc = result["encoding"].lower()
            enc = self._normalize_cjk_detection(enc, sample)
            return (enc, result.get("confidence", 0.0))

        return ("unknown", 0.0)

    @staticmethod
    def _normalize_cjk_detection(encoding, sample):
        # type: (str, bytes) -> str
        # charset_normalizer sometimes misidentifies CJK encodings for short text.
        # CP949 (Korean) is often confused with GBK (Chinese) when the text is Chinese.
        # We try to disambiguate by attempting to decode as GBK first.
        if encoding == "cp949":
            try:
                sample.decode("gbk")
                sample.decode("cp949")
                # Both work - check if GBK is a better fit by seeing if cp949 loses chars
                gbk_decoded = sample.decode("gbk")
                try:
                    cp949_decoded = sample.decode("cp949")
                    if len(gbk_decoded) >= len(cp949_decoded):
                        return "gbk"
                except Exception:
                    return "gbk"
            except Exception:
                pass
        if encoding == "euc_kr":
            try:
                sample.decode("gbk")
                return "gbk"
            except Exception:
                pass
        return encoding

    def _read_sample(self, file_path):
        # type: (str) -> bytes
        try:
            with open(file_path, "rb") as f:
                return f.read(SAMPLE_SIZE)
        except (IOError, OSError):
            return b""

    def _detect_bom(self, sample):
        # type: (bytes) -> Optional[str]
        BOM_MARKERS = [
            (b'\x00\x00\xfe\xff', 'utf-32-be'),
            (b'\xff\xfe\x00\x00', 'utf-32-le'),
            (b'\xfe\xff', 'utf-16-be'),
            (b'\xff\xfe', 'utf-16-le'),
            (b'\xef\xbb\xbf', 'utf-8-sig'),
        ]
        for marker, encoding in BOM_MARKERS:
            if sample.startswith(marker):
                return encoding
        return None

    @staticmethod
    def is_likely_binary(sample):
        # type: (bytes) -> bool
        check_region = sample[:8192]
        return b'\x00' in check_region
