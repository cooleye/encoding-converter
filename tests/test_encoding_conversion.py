import os
import tempfile
import pytest
import codecs

from src.core.converter import EncodingConverter
from src.core.models import ConversionConfig, ErrorStrategy
from src.utils.encoding_list import get_all_encodings


class TestEncodingBidirectional:
    """测试所有编码是否支持双向互转"""

    @pytest.fixture
    def temp_dir(self):
        """创建临时目录"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    def get_test_text(self, encoding):
        """根据编码类型返回合适的测试文本"""
        if encoding in ('utf-8', 'utf-8-sig'):
            return "Hello 你好世界 こんにちは 안녕하세요 🔥"
        elif encoding in ('utf-16-le', 'utf-16-be', 'utf-32-le', 'utf-32-be'):
            return "Hello 你好世界 Test"
        elif encoding in ('gbk', 'gb2312', 'gb18030'):
            return "Hello 你好世界 测试文本"
        elif encoding in ('big5', 'big5hkscs'):
            return "Hello 你好世界 測試文字"
        elif encoding in ('shift_jis', 'euc_jp', 'iso2022_jp', 'cp932'):
            return "Hello こんにちは テスト"
        elif encoding in ('euc_kr', 'cp949', 'iso2022_kr'):
            return "Hello 안녕하세요 테스트"
        elif encoding in ('iso-8859-1', 'iso-8859-15', 'cp1252', 'ascii', 'mac_roman'):
            return "Hello World Test Text 123"
        elif encoding in ('koi8_r', 'koi8_u', 'cp1251', 'iso-8859-5'):
            return "Hello Привет мир Тест"
        elif encoding in ('cp1256', 'iso-8859-6'):
            return "Hello Test 123"
        elif encoding in ('cp1253', 'iso-8859-7'):
            return "Hello Test 123"
        elif encoding in ('cp1255', 'iso-8859-8'):
            return "Hello Test 123"
        elif encoding in ('iso-8859-2', 'iso-8859-3', 'iso-8859-4', 'cp1250'):
            return "Hello Zdravo Test 123"
        elif encoding in ('cp1254',):
            return "Hello Merhaba Test 123"
        elif encoding in ('cp1257',):
            return "Hello Sveiki Test 123"
        elif encoding in ('cp1258',):
            return "Hello Xin chao Test 123"
        elif encoding in ('tis_620',):
            return "Hello Test 123"
        else:
            return "Hello World Test 123"

    def test_all_encodings_registered(self):
        """测试所有编码是否在 Python 中注册"""
        all_encodings = get_all_encodings()
        unsupported = []
        
        for display_name, codec_name in all_encodings:
            try:
                codecs.lookup(codec_name)
            except LookupError:
                unsupported.append((display_name, codec_name))
        
        if unsupported:
            pytest.fail(
                "以下编码不被 Python 支持:\n" + 
                "\n".join([f"  {name} ({codec})" for name, codec in unsupported])
            )

    def test_encoding_roundtrip(self, temp_dir):
        """测试编码往返转换：创建文件 -> 读取 -> 验证内容"""
        all_encodings = get_all_encodings()
        failed = []
        
        for display_name, codec_name in all_encodings:
            test_text = self.get_test_text(codec_name)
            
            try:
                test_file = os.path.join(temp_dir, f"test_{codec_name}.txt")
                
                with open(test_file, 'w', encoding=codec_name, errors='replace') as f:
                    f.write(test_text)
                
                with open(test_file, 'r', encoding=codec_name, errors='replace') as f:
                    read_text = f.read()
                
                if test_text != read_text:
                    failed.append((display_name, codec_name, "写入后读取内容不匹配"))
                    
            except Exception as e:
                failed.append((display_name, codec_name, str(e)))
        
        if failed:
            pytest.fail(
                "以下编码往返测试失败:\n" + 
                "\n".join([f"  {name} ({codec}): {msg}" for name, codec, msg in failed])
            )

    def test_encoding_to_utf8_conversion(self, temp_dir):
        """测试从各编码转换到 UTF-8"""
        all_encodings = get_all_encodings()
        failed = []
        skipped_encodings = ['utf-16-le', 'utf-16-be', 'utf-32-le', 'utf-32-be']
        
        for display_name, codec_name in all_encodings:
            if codec_name in skipped_encodings:
                continue
                
            test_text = self.get_test_text(codec_name)
            
            try:
                original_file = os.path.join(temp_dir, f"test_{codec_name}_original.txt")
                
                with open(original_file, 'w', encoding=codec_name, errors='replace') as f:
                    f.write(test_text)
                
                config = ConversionConfig(
                    source_encoding=codec_name,
                    target_encoding='utf-8',
                    auto_detect=False,
                    create_backup=False,
                    error_strategy=ErrorStrategy.REPLACE,
                )
                converter = EncodingConverter(config)
                result = converter.convert_file(original_file)
                
                if not result.success:
                    failed.append((display_name, codec_name, f"转换失败: {result.error_message}"))
                    continue
                
                with open(original_file, 'r', encoding='utf-8', errors='replace') as f:
                    content = f.read()
                
                if "Hello" not in content:
                    failed.append((display_name, codec_name, "转换后内容异常"))
                    
            except Exception as e:
                failed.append((display_name, codec_name, str(e)))
        
        if failed:
            pytest.fail(
                "以下编码转换到UTF-8失败:\n" + 
                "\n".join([f"  {name} ({codec}): {msg}" for name, codec, msg in failed])
            )

    def test_utf8_to_other_encoding_conversion(self, temp_dir):
        """测试从 UTF-8 转换到其他编码"""
        target_encodings = [
            ('GBK', 'gbk'),
            ('Big5', 'big5'),
            ('Shift-JIS', 'shift_jis'),
            ('ISO-8859-1', 'iso-8859-1'),
            ('Windows-1252', 'cp1252'),
        ]
        failed = []
        
        for display_name, codec_name in target_encodings:
            test_text = "Hello World Test 123"
            
            try:
                test_file = os.path.join(temp_dir, f"test_utf8_to_{codec_name}.txt")
                
                with open(test_file, 'w', encoding='utf-8') as f:
                    f.write(test_text)
                
                config = ConversionConfig(
                    source_encoding='utf-8',
                    target_encoding=codec_name,
                    auto_detect=False,
                    create_backup=False,
                    error_strategy=ErrorStrategy.REPLACE,
                )
                converter = EncodingConverter(config)
                result = converter.convert_file(test_file)
                
                if not result.success:
                    failed.append((display_name, codec_name, f"转换失败: {result.error_message}"))
                    continue
                
                with open(test_file, 'rb') as f:
                    raw = f.read()
                
                decoded = raw.decode(codec_name, errors='replace')
                if "Hello" not in decoded:
                    failed.append((display_name, codec_name, "转换后内容异常"))
                    
            except Exception as e:
                failed.append((display_name, codec_name, str(e)))
        
        if failed:
            pytest.fail(
                "以下编码从UTF-8转换失败:\n" + 
                "\n".join([f"  {name} ({codec}): {msg}" for name, codec, msg in failed])
            )

    def test_encoding_pairwise_conversion(self, temp_dir):
        """测试常用编码之间的两两转换"""
        common_encodings = [
            ('UTF-8', 'utf-8'),
            ('GBK', 'gbk'),
            ('Big5', 'big5'),
            ('Shift-JIS', 'shift_jis'),
            ('ISO-8859-1', 'iso-8859-1'),
        ]
        
        failed = []
        
        for src_name, src_codec in common_encodings:
            for tgt_name, tgt_codec in common_encodings:
                if src_codec == tgt_codec:
                    continue
                
                test_text = "Hello World 123"
                
                try:
                    test_file = os.path.join(temp_dir, f"test_{src_codec}_to_{tgt_codec}.txt")
                    
                    with open(test_file, 'w', encoding=src_codec, errors='replace') as f:
                        f.write(test_text)
                    
                    config = ConversionConfig(
                        source_encoding=src_codec,
                        target_encoding=tgt_codec,
                        auto_detect=False,
                        create_backup=False,
                        error_strategy=ErrorStrategy.REPLACE,
                    )
                    converter = EncodingConverter(config)
                    result = converter.convert_file(test_file)
                    
                    if not result.success:
                        failed.append(f"{src_name} -> {tgt_name}: {result.error_message}")
                    
                except Exception as e:
                    failed.append(f"{src_name} -> {tgt_name}: {str(e)}")
        
        if failed:
            pytest.fail(
                "以下编码对转换测试失败:\n" + 
                "\n".join([f"  {msg}" for msg in failed])
            )


class TestBatchConversion:
    """测试批量转换功能"""

    @pytest.fixture
    def temp_dir(self):
        """创建临时目录"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    def test_batch_convert_multiple_files(self, temp_dir):
        """测试批量转换多个文件"""
        files = []
        for i in range(5):
            file_path = os.path.join(temp_dir, f"test_{i}.txt")
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f"测试文件 {i}\nHello World {i}")
            files.append(file_path)
        
        config = ConversionConfig(
            source_encoding='utf-8',
            target_encoding='gbk',
            auto_detect=False,
            create_backup=False,
            error_strategy=ErrorStrategy.REPLACE,
        )
        
        converter = EncodingConverter(config)
        results = []
        
        for file_path in files:
            result = converter.convert_file(file_path)
            results.append(result)
        
        success_count = sum(1 for r in results if r.success)
        assert success_count == 5, f"只有 {success_count}/5 个文件转换成功"
        
        for file_path in files:
            with open(file_path, 'r', encoding='gbk') as f:
                content = f.read()
            assert "Hello World" in content

    def test_batch_convert_with_backup(self, temp_dir):
        """测试批量转换时创建备份"""
        files = []
        for i in range(3):
            file_path = os.path.join(temp_dir, f"test_backup_{i}.txt")
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f"原始内容 {i}")
            files.append(file_path)
        
        config = ConversionConfig(
            source_encoding='utf-8',
            target_encoding='gbk',
            auto_detect=False,
            create_backup=True,
            error_strategy=ErrorStrategy.REPLACE,
        )
        
        converter = EncodingConverter(config)
        
        for file_path in files:
            result = converter.convert_file(file_path)
            assert result.success, f"转换失败: {result.error_message}"
            assert result.backup_path is not None, "未创建备份文件"
            assert os.path.exists(result.backup_path), "备份文件不存在"
        
        for file_path in files:
            backup_path = file_path + ".bak"
            with open(backup_path, 'r', encoding='utf-8') as f:
                backup_content = f.read()
            assert "原始内容" in backup_content

    def test_batch_convert_mixed_encodings(self, temp_dir):
        """测试批量转换不同编码的文件"""
        test_cases = [
            ('utf-8', 'UTF-8 测试'),
            ('gbk', 'GBK 测试'),
            ('big5', 'Big5 測試'),
        ]
        
        files = []
        for encoding, content in test_cases:
            file_path = os.path.join(temp_dir, f"test_{encoding}.txt")
            with open(file_path, 'w', encoding=encoding, errors='replace') as f:
                f.write(content)
            files.append((file_path, encoding))
        
        config = ConversionConfig(
            source_encoding='',
            target_encoding='utf-8',
            auto_detect=True,
            create_backup=False,
            error_strategy=ErrorStrategy.REPLACE,
        )
        
        converter = EncodingConverter(config)
        results = []
        
        for file_path, original_encoding in files:
            result = converter.convert_file(file_path)
            results.append((result, original_encoding))
        
        for result, original_encoding in results:
            assert result.success, f"转换失败 (原编码: {original_encoding}): {result.error_message}"

    def test_batch_convert_large_files(self, temp_dir):
        """测试批量转换大文件"""
        large_content = "测试大文件内容\n" * 10000
        
        files = []
        for i in range(3):
            file_path = os.path.join(temp_dir, f"large_{i}.txt")
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(large_content)
            files.append(file_path)
        
        config = ConversionConfig(
            source_encoding='utf-8',
            target_encoding='gbk',
            auto_detect=False,
            create_backup=False,
            error_strategy=ErrorStrategy.REPLACE,
        )
        
        converter = EncodingConverter(config)
        
        for file_path in files:
            result = converter.convert_file(file_path)
            assert result.success, f"大文件转换失败: {result.error_message}"
            assert result.bytes_processed > 0, "未处理任何字节"

    def test_batch_convert_with_progress(self, temp_dir):
        """测试批量转换时的进度回调"""
        file_path = os.path.join(temp_dir, "progress_test.txt")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write("测试进度回调")
        
        config = ConversionConfig(
            source_encoding='utf-8',
            target_encoding='gbk',
            auto_detect=False,
            create_backup=False,
            error_strategy=ErrorStrategy.REPLACE,
        )
        
        converter = EncodingConverter(config)
        progress_values = []
        
        def progress_callback(progress):
            progress_values.append(progress)
        
        result = converter.convert_file(file_path, progress_callback=progress_callback)
        
        assert result.success, f"转换失败: {result.error_message}"
        assert len(progress_values) > 0, "未收到进度回调"
        assert progress_values[-1] == 100, f"最终进度不是100: {progress_values[-1]}"
