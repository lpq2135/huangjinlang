import os
import sys
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime


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
    current_date = datetime.now().strftime("%Y-%m-%d")
    log_file = os.path.join(log_folder, f'my_log_{current_date}.log')  # 使用当前日期作为文件名
    file_handler = RotatingFileHandler(log_file, maxBytes=100 * 1024 * 1024,
                                       backupCount=10)  # 设置每个日志文件大小为10MB，保留最近10个日志文件
    file_handler.setFormatter(logging.Formatter(log_format))

    # 获取 root logger，并设置级别
    logger = logging.getLogger('')
    logger.setLevel(level)  # 将 logger 的级别设为 INFO
    logger.addHandler(console)
    logger.addHandler(file_handler)
