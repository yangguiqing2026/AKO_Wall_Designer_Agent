"""几何导出工具模块 - 2D线稿/深度图渲染."""

from typing import Any

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from src.utils.logging import get_logger

logger = get_logger(__name__)


def render_lineart(
    wall_length: float,
    wall_height: float,
    columns: list[dict[str, Any]],
    panels: list[dict[str, Any]],
    scale: float = 1.0,
) -> Image.Image:
    """渲染围墙2D立面线稿.

    Args:
        wall_length: 围墙总长 (mm)
        wall_height: 围墙总高 (mm)
        columns: 柱数据列表
        panels: 面板数据列表
        scale: 像素缩放比例

    Returns:
        PIL Image 线稿图
    """
    # 画布大小
    max_pixels = 4096
    mm_per_pixel = 2.0 / scale

    img_width = min(int(wall_length / mm_per_pixel) + 100, max_pixels)
    img_height = min(int(wall_height / mm_per_pixel) + 200, max_pixels)

    # 创建白色画布
    img = Image.new("RGB", (img_width, img_height), color="white")
    draw = ImageDraw.Draw(img)

    # 绘图偏移 (底部留150px)
    offset_y = img_height - 150

    # 颜色定义
    column_color = (80, 80, 80)
    panel_color = (40, 40, 40)
    grid_color = (200, 200, 200)

    # 绘制水平网格线
    for y_mm in range(0, int(wall_height) + 600, 600):
        y_px = offset_y - int(y_mm / mm_per_pixel)
        if 0 <= y_px <= img_height:
            draw.line([(0, y_px), (img_width, y_px)], fill=grid_color, width=1)

    # 绘制柱
    for col in columns:
        cx = col.get("position_x", 0)
        cw = col.get("width", 300)
        ch = col.get("height", wall_height)

        x1 = int(cx / mm_per_pixel) - int(cw / 2 / mm_per_pixel) + 50
        y1 = offset_y - int(ch / mm_per_pixel)
        x2 = int(cx / mm_per_pixel) + int(cw / 2 / mm_per_pixel) + 50
        y2 = offset_y

        draw.rectangle([x1, y1, x2, y2], fill=column_color, outline=(30, 30, 30), width=2)

        # 柱标签
        try:
            draw.text(
                (x1 + 5, y1 + 5),
                f"C{col.get('index', '')}",
                fill=(255, 255, 255),
            )
        except Exception:
            pass

    # 绘制面板
    for panel in panels:
        px = panel.get("position_x", 0)
        py = panel.get("position_y", 0)
        pw = panel.get("width", 600)
        ph = panel.get("height", 2400)

        x1 = int(px / mm_per_pixel) - int(pw / 2 / mm_per_pixel) + 50
        y1 = offset_y - int((py + ph / 2) / mm_per_pixel)
        x2 = int(px / mm_per_pixel) + int(pw / 2 / mm_per_pixel) + 50
        y2 = offset_y - int((py - ph / 2) / mm_per_pixel)

        is_standard = panel.get("is_standard", True)
        outline = (0, 0, 0) if is_standard else (200, 0, 0)

        draw.rectangle([x1, y1, x2, y2], fill=panel_color, outline=outline, width=1)

        # 非标板标记
        if not is_standard:
            draw.text((x1 + 2, y1 + 2), "NS", fill=(255, 0, 0))

    # 绘制地面线
    draw.line([(0, offset_y), (img_width, offset_y)], fill=(0, 0, 0), width=3)

    logger.info(f"线稿渲染: {img_width}×{img_height}px")
    return img


def render_depth_map(
    wall_length: float,
    wall_height: float,
    columns: list[dict[str, Any]],
    panels: list[dict[str, Any]],
) -> np.ndarray:
    """渲染围墙深度图 (用于 ControlNet Depth).

    Args:
        wall_length: 围墙总长 (mm)
        wall_height: 围墙总高 (mm)
        columns: 柱数据列表
        panels: 面板数据列表

    Returns:
        深度图 numpy 数组 (H×W, 0-255)
    """
    # 首先生成线稿
    lineart = render_lineart(wall_length, wall_height, columns, panels, scale=0.5)

    # 转换为灰度深度图
    depth = lineart.convert("L")
    depth_array = np.array(depth)

    # 反转: 白色(255)=远, 黑色(0)=近
    depth_array = 255 - depth_array

    logger.info(f"深度图渲染: {depth_array.shape}")
    return depth_array


def export_to_stl(
    modular_result: dict[str, Any],
    column_design: dict[str, Any],
    foundation_design: dict[str, Any],
    filepath: str,
) -> bool:
    """导出围墙3D模型为STL文件 (便捷函数).

    Args:
        modular_result: 模数计算结果
        column_design: 柱设计结果
        foundation_design: 基础设计结果
        filepath: 输出路径

    Returns:
        成功返回 True
    """
    from src.geometry.wall_generator import WallGeometryGenerator

    generator = WallGeometryGenerator(modular_result, column_design, foundation_design)
    return generator.export_to_stl(str(filepath))