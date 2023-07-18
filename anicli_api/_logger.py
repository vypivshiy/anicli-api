import colorlog


__all__ = ["logger"]



logger = colorlog.getLogger("anicli-api")
logger.setLevel(colorlog.INFO)

formatter = colorlog.ColoredFormatter(fmt="%(log_color)s %(asctime)s [anicli-api] [%(levelname)-8s]"
                                          " %(name)s: %(message)s'")

stdout_handler = colorlog.StreamHandler()
stdout_handler.setFormatter(formatter)
logger.addHandler(stdout_handler)


sc_schema_logger = colorlog.getLogger("scrape_schema")
sc_schema_logger.setLevel(colorlog.ERROR)
