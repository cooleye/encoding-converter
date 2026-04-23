import logging
import os
import sys


def setup_logging(level=logging.INFO):
    # type: (int) -> logging.Logger
    logger = logging.getLogger("encoding_converter")
    logger.setLevel(level)

    if not logger.handlers:
        console = logging.StreamHandler(sys.stdout)
        console.setLevel(level)
        fmt = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%H:%M:%S",
        )
        console.setFormatter(fmt)
        logger.addHandler(console)

        log_dir = os.path.join(os.path.expanduser("~"), ".encoding_converter")
        try:
            os.makedirs(log_dir, exist_ok=True)
            log_file = os.path.join(log_dir, "converter.log")
            file_handler = logging.FileHandler(log_file, encoding="utf-8")
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(fmt)
            logger.addHandler(file_handler)
        except (IOError, OSError):
            pass

    return logger
