import os
import pytest
from src.core.bom_handler import detect_bom, strip_bom, get_bom_for_encoding, has_bom


class TestBomHandler:

    def test_detect_utf8_bom(self, utf8_bom_file):
        result = detect_bom(utf8_bom_file)
        assert result is not None
        assert result[0] == "utf-8-sig"
        assert result[1] == 3

    def test_detect_no_bom(self, utf8_file):
        result = detect_bom(utf8_file)
        assert result is None

    def test_strip_utf8_bom(self):
        content = b'\xef\xbb\xbfHello World'
        stripped, was_bom = strip_bom(content)
        assert was_bom is True
        assert stripped == b'Hello World'

    def test_strip_no_bom(self):
        content = b'Hello World'
        stripped, was_bom = strip_bom(content)
        assert was_bom is False
        assert stripped == content

    def test_get_bom_for_utf8(self):
        bom = get_bom_for_encoding("utf-8")
        assert bom == b'\xef\xbb\xbf'

    def test_get_bom_for_utf16_be(self):
        bom = get_bom_for_encoding("utf-16-be")
        assert bom == b'\xfe\xff'

    def test_get_bom_for_unknown(self):
        bom = get_bom_for_encoding("gbk")
        assert bom is None

    def test_has_bom_true(self, utf8_bom_file):
        assert has_bom(utf8_bom_file) is True

    def test_has_bom_false(self, utf8_file):
        assert has_bom(utf8_file) is False
