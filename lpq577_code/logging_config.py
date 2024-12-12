import logging


def setup_logger():
    # 设置日志
    log_format = '%(asctime)s - %(levelname)s - %(message)s'
    level = logging.INFO

    # 控制台日志
    console = logging.StreamHandler()
    console.setLevel(level)
    console.setFormatter(logging.Formatter(log_format))

    # 获取 root logger，并设置级别
    logger = logging.getLogger('')
    logger.setLevel(level)  # 将 logger 的级别设为 INFO
    logger.addHandler(console)