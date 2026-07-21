"""日志管理模块."""

import logging
import sys
from typing import Optional


def setup_logging(level: str = "INFO", log_file: Optional[str] = None) -> logging.Logger:
    """配置并返回根日志记录器.

    Args:
        level: 日志级别 (DEBUG/INFO/WARNING/ERROR)
        log_file: 可选日志文件路径

    Returns:
        配置完毕的根 Logger
    """
    logger = logging.getLogger("ako_wall_designer")
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # 控制台 Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_format = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)

    # 文件 Handler (可选)
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_format = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | %(filename)s:%(lineno)d | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler.setFormatter(file_format)
        logger.addHandler(file_handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    """获取子日志记录器.

    Args:
        name: 模块名称，自动添加前缀

    Returns:
        子 Logger 实例
    """
    return logging.getLogger(f"ako_wall_designer.{name}")