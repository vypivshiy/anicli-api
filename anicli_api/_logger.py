import logging

import colorlog

__all__ = ["logger"]


handler = colorlog.StreamHandler()
_formatter = colorlog.ColoredFormatter(fmt="%(log_color)s %(asctime)s [%(levelname)-8s] %(name)s: %(message)s'")

logger = logging.getLogger("anicli-api")  # type: ignore
logger.addHandler(handler)
logger.setLevel(logging.INFO)


_logger_cast = logging.getLogger("type_caster")
_logger_cast.setLevel(logging.ERROR)  # type: ignore

_sc_schema_logger = logging.getLogger("scrape_schema")
_sc_schema_logger.setLevel(logging.ERROR)
