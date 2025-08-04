# utils/logging_utils.py
import logging
import os
import datetime

def setup_logger(log_file: str | None = None, level=logging.INFO):
    """
    Initialise Python's root logger.  If log_file is None, create a unique
    timestamped log in a 'logs' directory.
    """
    if log_file is None:
        log_dir = "logs"
        os.makedirs(log_dir, exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = os.path.join(log_dir, f"drone_{timestamp}.log")

    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    logging.info(f"Logging to: {log_file}")

