import logging

LOG_FORMAT = '%(asctime)s %(name)s %(module)s:%(lineno)d %(levelname)s %(message)s'
LOG_FILE = '/tmp/cals.log'

def getLogger(name):
    log_formatter = logging.Formatter(LOG_FORMAT)
    log_handler = logging.FileHandler(LOG_FILE, 'a+')
    log_handler.setFormatter(log_formatter)
    logger = logging.getLogger(name)
    logger.addHandler(log_handler)
    return logger
