import os
import tempfile
import pytest


@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as d:
        yield d


@pytest.fixture
def gbk_file(temp_dir):
    path = os.path.join(temp_dir, "test_gbk.txt")
    content = "这是GBK编码的中文文本\n第二行文字\n"
    with open(path, "w", encoding="gbk") as f:
        f.write(content)
    return path


@pytest.fixture
def utf8_bom_file(temp_dir):
    path = os.path.join(temp_dir, "test_utf8bom.txt")
    content = "UTF-8 with BOM\n"
    with open(path, "w", encoding="utf-8-sig") as f:
        f.write(content)
    return path


@pytest.fixture
def utf8_file(temp_dir):
    path = os.path.join(temp_dir, "test_utf8.txt")
    content = "Plain UTF-8 text\nSecond line\n"
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path


@pytest.fixture
def large_file(temp_dir):
    path = os.path.join(temp_dir, "large_test.txt")
    line = "A" * 100 + "\n"
    with open(path, "w", encoding="utf-8") as f:
        for _ in range(110000):
            f.write(line)
    return path


@pytest.fixture
def binary_file(temp_dir):
    path = os.path.join(temp_dir, "test_binary.bin")
    with open(path, "wb") as f:
        f.write(b'\x89PNG\r\n\x1a\n' + b'\x00' * 100)
    return path
