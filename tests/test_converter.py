import os
import pytest
from src.core.converter import EncodingConverter
from src.core.models import ConversionConfig, ErrorStrategy
from src.core.bom_handler import has_bom


class TestEncodingConverter:

    def test_gbk_to_utf8(self, gbk_file):
        config = ConversionConfig(
            source_encoding="gbk",
            target_encoding="utf-8",
            auto_detect=False,
            create_backup=False,
        )
        converter = EncodingConverter(config)
        result = converter.convert_file(gbk_file)
        assert result.success
        with open(gbk_file, "r", encoding="utf-8") as f:
            assert "中文" in f.read()

    def test_auto_detect_and_convert(self, gbk_file):
        config = ConversionConfig(auto_detect=True, target_encoding="utf-8", create_backup=False)
        converter = EncodingConverter(config)
        result = converter.convert_file(gbk_file)
        assert result.success
        assert result.source_encoding in ("gbk", "gb2312", "gb18030", "cp949")

    def test_same_encoding_skip(self, utf8_file):
        config = ConversionConfig(
            source_encoding="utf-8",
            target_encoding="utf-8",
            create_backup=False,
        )
        converter = EncodingConverter(config)
        result = converter.convert_file(utf8_file)
        assert result.skipped

    def test_binary_file_rejected(self, binary_file):
        config = ConversionConfig(target_encoding="utf-8")
        converter = EncodingConverter(config)
        result = converter.convert_file(binary_file)
        assert not result.success
        assert "binary" in result.error_message.lower()

    def test_backup_created(self, utf8_file):
        config = ConversionConfig(
            source_encoding="utf-8",
            target_encoding="gbk",
            create_backup=True,
        )
        converter = EncodingConverter(config)
        result = converter.convert_file(utf8_file)
        assert result.success
        assert result.backup_path is not None
        assert os.path.exists(result.backup_path)

    def test_bom_strip(self, utf8_bom_file):
        config = ConversionConfig(
            target_encoding="utf-8",
            strip_bom=True,
            create_backup=False,
        )
        converter = EncodingConverter(config)
        result = converter.convert_file(utf8_bom_file)
        assert result.success
        assert not has_bom(utf8_bom_file)

    def test_bom_add(self, utf8_file):
        config = ConversionConfig(
            target_encoding="utf-8-sig",
            add_bom=True,
            create_backup=False,
        )
        converter = EncodingConverter(config)
        result = converter.convert_file(utf8_file)
        assert result.success
        assert has_bom(utf8_file)

    def test_large_file_streaming(self, large_file):
        config = ConversionConfig(
            source_encoding="utf-8",
            target_encoding="gbk",
            error_strategy=ErrorStrategy.REPLACE,
            create_backup=False,
        )
        converter = EncodingConverter(config)
        result = converter.convert_file(large_file)
        assert result.success

    def test_progress_callback(self, utf8_file):
        progress_values = []

        def cb(p):
            progress_values.append(p)

        config = ConversionConfig(
            source_encoding="utf-8",
            target_encoding="gbk",
            create_backup=False,
        )
        converter = EncodingConverter(config)
        result = converter.convert_file(utf8_file, progress_callback=cb)
        assert result.success
        assert len(progress_values) > 0

    def test_nonexistent_file(self):
        config = ConversionConfig(target_encoding="utf-8")
        converter = EncodingConverter(config)
        result = converter.convert_file("/nonexistent/path/file.txt")
        assert not result.success

    def test_utf8_to_gbk_and_back(self, utf8_file):
        config = ConversionConfig(
            source_encoding="utf-8",
            target_encoding="gbk",
            create_backup=False,
        )
        converter = EncodingConverter(config)
        result = converter.convert_file(utf8_file)
        assert result.success

        with open(utf8_file, "r", encoding="gbk") as f:
            content = f.read()
        assert "Plain" in content

        config2 = ConversionConfig(
            source_encoding="gbk",
            target_encoding="utf-8",
            create_backup=False,
        )
        converter2 = EncodingConverter(config2)
        result2 = converter2.convert_file(utf8_file)
        assert result2.success

        with open(utf8_file, "r", encoding="utf-8") as f:
            final_content = f.read()
        assert "Plain UTF-8 text" in final_content
