from sys import stdout

from loguru import logger


logger.remove()
logger.add(
    stdout,
    level='DEBUG',
    format='<green>{time:DD-MM-YYYY HH:mm:ss}</> | ' 
        '<lvl>{level}</> | <blue>{module}:{function}</> | ' 
        '<lvl>{message}</> {exception}',
    colorize=True
)