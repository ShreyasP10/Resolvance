import logging

def get_logger(name: str = "sentinel"):
    return logging.getLogger(name)

def configure_logging(level=logging.INFO):
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    )
