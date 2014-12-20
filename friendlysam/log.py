import logging

root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)

stderr_handler = logging.StreamHandler()
stderr_handler.setFormatter(logging.Formatter('[%(levelname)8s] (%(name)s) %(message)s'))
root_logger.addHandler(stderr_handler)

def get_logger(name):
    return root_logger.getChild(name)