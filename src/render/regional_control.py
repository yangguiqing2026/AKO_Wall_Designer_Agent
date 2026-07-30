# ============================================
# Author: AKO_studio
# Agent: AKO_wall_designer_agent
# Generated: 2026-07-30
# ============================================
#
"""区域控制渲染模块 - 按不同区域应用不同材质 LoRA."""

import numpy as np
from PIL import Image

from src.materials.material_library import MaterialLibrary
from src.utils.logging import get_logger

logger = get_logger(__name__)


class RegionalControlRenderer:
    """区域控制渲染器 - 对不同区域（墙板/柱）应用不同材质.

    通过 mask 控制不同区域的材质应用，实现墙板和柱的材质区分。
    """

    def __init__(self):
        """初始化区域控制渲染器."""
        self.material_lib = MaterialLibrary()

    def create_region_mask(
        self,
        wall_length: float,
        wall_height: float,
        columns: list[dict],
        image_size: tuple[int, int] = (2048, 1536),
    ) -> np.ndarray:
        """创建区域掩码图像.

        Args:
            wall_length: 围墙总长 (mm)
            wall_height: 围墙总高 (mm)
            columns: 柱数据
            image_size: 掩码图像尺寸

        Returns:
            掩码数组 (H×W)，0=墙板区域, 1=柱区域, 2=其他
        """
        mask = np.zeros((image_size[1], image_size[0]), dtype=np.uint8)

        scale_x = image_size[0] / wall_length if wall_length > 0 else 1
        scale_y = image_size[1] / wall_height if wall_height > 0 else 1

        # 标记柱区域
        for col in columns:
            cx = col.get("position_x", 0)
            cw = col.get("width", 300)
            ch = col.get("height", wall_height)

            x1 = max(0, int((cx - cw / 2) * scale_x))
            x2 = min(image_size[0], int((cx + cw / 2) * scale_x))
            y1 = max(0, image_size[1] - int(ch * scale_y))
            y2 = image_size[1]

            if 0 <= x1 < image_size[0] and 0 <= x2 <= image_size[0]:
                mask[y1:y2, x1:x2] = 1

        # 标记墙板区域 (柱之外的空白墙区域默认为0)
        # mask 中 0=墙板, 1=柱, 2=背景

        return mask

    def apply_material_by_region(
        self,
        rendered_image: Image.Image,
        mask: np.ndarray,
        wall_material_name: str,
        column_material_name: str,
    ) -> Image.Image:
        """根据区域掩码应用不同材质.

        Args:
            rendered_image: 已渲染的图像
            mask: 区域掩码
            wall_material_name: 墙板材质名称
            column_material_name: 柱材质名称

        Returns:
            材质区分后的图像
        """
        wall_mat = self.material_lib.get_material(wall_material_name)
        column_mat = self.material_lib.get_material(column_material_name)

        if wall_mat is None or column_mat is None:
            logger.warning("材质未找到，使用原始图像")
            return rendered_image

        # 这里在实际部署中会调用 LoRA 加载器和图像处理
        # 当前返回原始图像作为占位实现
        logger.info(
            f"区域材质: 墙={wall_mat.display_name}, 柱={column_mat.display_name}"
        )
        return rendered_image