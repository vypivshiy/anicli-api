import logging

FORMAT_LOG = '%(asctime)s :: %(name)s :: %(levelname)s :: %(message)s'
LEVEL = logging.DEBUG

logger = logging.getLogger("anicli-api")
logger.setLevel(LEVEL)
formatter = logging.Formatter(fmt=FORMAT_LOG, datefmt='%d-%m-%Y %H:%M:%S')
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
console_handler.setLevel(LEVEL)
logger.addHandler(console_handler)
