import codecs
import os
import shutil
from datetime import datetime
from typing import Optional, Callable, Tuple, List

from .models import ConversionConfig, ConversionResult, ErrorStrategy
from .bom_handler import strip_bom, get_bom_for_encoding, detect_bom, BOM_TABLE
from .detector import EncodingDetector

LARGE_FILE_THRESHOLD = 10 * 1024 * 1024
STREAM_CHUNK_SIZE = 64 * 1024
PREVIEW_SAMPLE_SIZE = 512 * 1024


class EncodingConverter(object):

    def __init__(self, config):
        # type: (ConversionConfig) -> None
        self.config = config
        self.detector = EncodingDetector()
        self._cancelled = False
        self._session_dir = None  # type: Optional[str]

    def cancel(self):
        # type: () -> None
        self._cancelled = True

    def get_session_dir(self):
        # type: () -> str
        if self._session_dir is None:
            base_dir = self.config.get_effective_output_dir()
            timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
            self._session_dir = os.path.join(base_dir, timestamp)
            os.makedirs(self._session_dir, exist_ok=True)
        return self._session_dir

    def convert_file(self, file_path, detected_encoding=None, progress_callback=None):
        # type: (str, Optional[str], Optional[Callable[[int], None]]) -> ConversionResult
        result = ConversionResult(
            file_path=file_path,
            success=False,
            source_encoding="",
            target_encoding=self.config.target_encoding,
        )

        try:
            self._validate_file(file_path)

            if self.config.auto_detect and not detected_encoding:
                detected_encoding, _ = self.detector.detect(file_path)
            source_enc = (
                detected_encoding
                if (self.config.keep_per_file_encoding or self.config.auto_detect)
                else self.config.source_encoding
            )
            if source_enc in ("unknown", ""):
                raise ValueError("Cannot determine encoding of {}".format(file_path))
            result.source_encoding = source_enc

            if self._should_skip(source_enc, file_path):
                session_dir = self.get_session_dir()
                output_path = self._get_output_path(file_path, session_dir)
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                shutil.copy2(file_path, output_path)
                result.skipped = True
                result.skip_reason = "Same encoding, copied to output"
                result.success = True
                result.output_path = output_path
                return result

            if progress_callback:
                progress_callback(10)

            if progress_callback:
                progress_callback(20)

            session_dir = self.get_session_dir()
            output_path = self._get_output_path(file_path, session_dir)
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            file_size = os.path.getsize(file_path)
            if file_size > LARGE_FILE_THRESHOLD:
                self._convert_large_file(file_path, source_enc, output_path, progress_callback)
            else:
                self._convert_small_file(file_path, source_enc, output_path, progress_callback)

            if progress_callback:
                progress_callback(100)

            result.success = True
            result.bytes_processed = file_size
            result.output_path = output_path

        except Exception as e:
            result.error_message = str(e)

        return result

    def _get_output_path(self, file_path, session_dir):
        # type: (str, str) -> str
        filename = os.path.basename(file_path)
        return os.path.join(session_dir, filename)

    def _validate_file(self, file_path):
        # type: (str) -> None
        if not os.path.exists(file_path):
            raise FileNotFoundError("File not found: {}".format(file_path))
        if not os.path.isfile(file_path):
            raise ValueError("Not a regular file: {}".format(file_path))
        if not os.access(file_path, os.R_OK):
            raise PermissionError("Cannot read file: {}".format(file_path))

        try:
            with open(file_path, 'rb') as f:
                sample = f.read(8192)
            if self.detector.is_likely_binary(sample):
                raise ValueError(
                    "File appears to be binary: {}. "
                    "Skipping to avoid data corruption.".format(file_path)
                )
        except (IOError, OSError) as e:
            raise IOError("Cannot read file for validation: {}".format(e))

    def _should_skip(self, source_enc, file_path):
        # type: (str, str) -> bool
        target_enc = self.config.target_encoding
        if self._normalize_enc(source_enc) != self._normalize_enc(target_enc):
            return False
        if self.config.strip_bom or self.config.add_bom:
            return False
        return True

    @staticmethod
    def _normalize_enc(enc):
        # type: (str) -> str
        e = enc.lower().replace("-", "").replace("_", "")
        if e in ("utf8", "utf8sig"):
            return "utf8"
        if e in ("gb2312", "gbk", "gb18030"):
            return "gbk"
        if e in ("ascii",):
            return "utf8"
        return e

    def _convert_small_file(self, file_path, source_enc, output_path, progress_callback):
        # type: (str, str, str, Optional[Callable[[int], None]]) -> None
        with open(file_path, 'rb') as f:
            raw = f.read()

        if progress_callback:
            progress_callback(40)

        if self.config.strip_bom:
            raw, _ = strip_bom(raw)

        text = raw.decode(source_enc, errors=self.config.error_strategy.value)

        if progress_callback:
            progress_callback(60)

        target_enc = self.config.target_encoding
        output = text.encode(target_enc, errors=self.config.error_strategy.value)

        if progress_callback:
            progress_callback(80)

        if self.config.add_bom:
            bom = get_bom_for_encoding(target_enc)
            if bom:
                output = bom + output

        temp_path = output_path + ".tmp"
        try:
            with open(temp_path, 'wb') as f:
                f.write(output)
            os.replace(temp_path, output_path)
        except Exception:
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except OSError:
                    pass
            raise

    def _convert_large_file(self, file_path, source_enc, output_path, progress_callback):
        # type: (str, str, str, Optional[Callable[[int], None]]) -> None
        target_enc = self.config.target_encoding
        file_size = os.path.getsize(file_path)
        temp_path = output_path + ".tmp"
        bytes_read = 0

        skip_bytes = 0
        if self.config.strip_bom:
            bom_info = detect_bom(file_path)
            if bom_info:
                skip_bytes = bom_info[1]

        output_bom = b""
        if self.config.add_bom:
            bom = get_bom_for_encoding(target_enc)
            if bom:
                output_bom = bom

        try:
            decoder = codecs.getincrementaldecoder(source_enc)(
                errors=self.config.error_strategy.value
            )
            encoder = codecs.getincrementalencoder(target_enc)(
                errors=self.config.error_strategy.value
            )
        except LookupError as e:
            raise ValueError("Unsupported encoding: {}".format(e))

        try:
            with open(file_path, 'rb') as fin, open(temp_path, 'wb') as fout:
                if output_bom:
                    fout.write(output_bom)

                if skip_bytes > 0:
                    fin.seek(skip_bytes)

                while True:
                    if self._cancelled:
                        raise InterruptedError("Conversion cancelled by user")

                    chunk = fin.read(STREAM_CHUNK_SIZE)
                    if not chunk:
                        break

                    decoded = decoder.decode(chunk, False)
                    encoded = encoder.encode(decoded, False)
                    fout.write(encoded)

                    bytes_read += len(chunk)
                    if progress_callback:
                        pct = 20 + int(70 * bytes_read / max(file_size, 1))
                        progress_callback(min(pct, 90))

                decoded = decoder.decode(b"", True)
                encoded = encoder.encode(decoded, True)
                if encoded:
                    fout.write(encoded)

            os.replace(temp_path, output_path)
        except Exception:
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except OSError:
                    pass
            raise

    def preview(self, file_path, source_enc, max_lines=200):
        # type: (str, str, int) -> Tuple[List[str], List[str], int]
        try:
            with open(file_path, 'rb') as f:
                raw = f.read(PREVIEW_SAMPLE_SIZE)
        except (IOError, OSError) as e:
            return ([], [], 0)

        if self.config.strip_bom:
            raw, _ = strip_bom(raw)

        original_text = raw.decode(source_enc, errors=self.config.error_strategy.value)
        original_lines = original_text.splitlines(keepends=True)[:max_lines]

        target_enc = self.config.target_encoding
        try:
            converted_text = original_text.encode(
                target_enc, errors=self.config.error_strategy.value
            ).decode(target_enc, errors=self.config.error_strategy.value)
        except Exception:
            converted_text = original_text
        converted_lines = converted_text.splitlines(keepends=True)[:max_lines]

        problem_count = sum(
            1 for line in converted_lines
            if '\ufffd' in line or '\\u' in line
        )

        return (original_lines, converted_lines, problem_count)
