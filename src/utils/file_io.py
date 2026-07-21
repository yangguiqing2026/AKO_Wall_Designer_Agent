"""文件读写工具模块."""

import json
from pathlib import Path
from typing import Any, Optional


def ensure_directory(path: Path) -> Path:
    """确保目录存在，不存在则创建.

    Args:
        path: 目标目录路径

    Returns:
        创建后的 Path 对象
    """
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_json(data: Any, filepath: Path, indent: int = 2) -> None:
    """将数据保存为 JSON 文件.

    Args:
        data: 要保存的数据
        filepath: 目标文件路径
        indent: JSON 缩进
    """
    filepath = Path(filepath)
    ensure_directory(filepath.parent)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=indent, default=str)


def load_json(filepath: Path) -> Any:
    """从 JSON 文件加载数据.

    Args:
        filepath: 源文件路径

    Returns:
        解析后的 Python 对象

    Raises:
        FileNotFoundError: 文件不存在
        json.JSONDecodeError: JSON 解析错误
    """
    filepath = Path(filepath)
    if not filepath.exists():
        raise FileNotFoundError(f"文件不存在: {filepath}")
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def save_text(content: str, filepath: Path) -> None:
    """保存文本文件.

    Args:
        content: 文本内容
        filepath: 目标文件路径
    """
    filepath = Path(filepath)
    ensure_directory(filepath.parent)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)


def load_text(filepath: Path) -> str:
    """读取文本文件.

    Args:
        filepath: 源文件路径

    Returns:
        文件全部文本内容
    """
    filepath = Path(filepath)
    if not filepath.exists():
        raise FileNotFoundError(f"文件不存在: {filepath}")
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()


def get_output_subdir(config, subdir: str) -> Path:
    """获取输出子目录路径并确保存在.

    Args:
        config: Config 实例
        subdir: 子目录名称

    Returns:
        子目录 Path 对象
    """
    path = config.output_path / subdir
    return ensure_directory(path)