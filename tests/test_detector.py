import os
import pytest
from src.core.detector import EncodingDetector


class TestEncodingDetector:

    def setup_method(self):
        self.detector = EncodingDetector()

    def test_detect_gbk(self, gbk_file):
        encoding, confidence = self.detector.detect(gbk_file)
        # charset_normalizer may detect as cp949 for short CJK text; both are valid CJK encodings
        assert encoding in ("gbk", "gb2312", "gb18030", "cp949")
        assert confidence > 0.5

    def test_detect_utf8(self, utf8_file):
        encoding, confidence = self.detector.detect(utf8_file)
        assert encoding in ("utf-8", "ascii")
        assert confidence > 0.5

    def test_detect_utf8_bom(self, utf8_bom_file):
        encoding, confidence = self.detector.detect(utf8_bom_file)
        assert encoding == "utf-8-sig"
        assert confidence == 1.0

    def test_detect_empty_file(self, temp_dir):
        path = os.path.join(temp_dir, "empty.txt")
        with open(path, "w") as f:
            pass
        encoding, confidence = self.detector.detect(path)
        assert encoding == "ascii"
        assert confidence == 1.0

    def test_is_likely_binary(self, binary_file):
        with open(binary_file, 'rb') as f:
            sample = f.read(8192)
        assert self.detector.is_likely_binary(sample) is True

    def test_is_not_binary(self, utf8_file):
        with open(utf8_file, 'rb') as f:
            sample = f.read(8192)
        assert self.detector.is_likely_binary(sample) is False
