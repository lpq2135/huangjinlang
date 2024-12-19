import os
import sys
import logging


def setup_logger():
    # 获取 .exe 文件的路径
    exe_path = os.path.dirname(sys.executable)

    # 在 .exe 文件的路径下创建 log 文件夹
    log_folder = os.path.join(exe_path, 'log')
    os.makedirs(log_folder, exist_ok=True)

    # 设置日志
    log_format = '%(asctime)s - %(levelname)s - %(message)s'
    level = logging.INFO

    # 控制台日志
    console = logging.StreamHandler()
    console.setLevel(level)
    console.setFormatter(logging.Formatter(log_format))

    # 文件日志
    log_file = os.path.join(log_folder, 'my_log.log')  # 用你希望的文件名替换 'my_log.log'
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(logging.Formatter(log_format))

    # 获取 root logger，并设置级别
    logger = logging.getLogger('')
    logger.setLevel(level)  # 将 logger 的级别设为 INFO
    logger.addHandler(console)
    logger.addHandler(file_handler)