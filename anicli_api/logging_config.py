import logging

FORMAT_LOG = "%(asctime)s :: %(name)s :: %(levelname)s :: %(message)s"


def init_logger(name: str, level: int = logging.CRITICAL):
    loger = logging.getLogger(name)
    loger.setLevel(level)
    formatter = logging.Formatter(fmt=FORMAT_LOG, datefmt="%d-%m-%Y %H:%M:%S")
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(level)
    loger.addHandler(console_handler)


init_logger("anicli-api")
logger = logging.getLogger("anicli-api.main")


if __name__ == "__main__":
    logger.debug("d")
    logger.info("i")
    logger.error("e")
    logger.warning("w")
    logger.critical("c")
