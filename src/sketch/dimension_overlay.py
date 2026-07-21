"""尺寸标注叠加模块."""

from PIL import Image, ImageDraw

from src.utils.logging import get_logger

logger = get_logger(__name__)


class DimensionOverlay:
    """尺寸标注叠加器 - 在草图上添加尺寸线和文字标注."""

    def __init__(self):
        """初始化标注叠加器."""
        pass

    def add_dimensions(self, image: Image.Image) -> Image.Image:
        """在图像上添加基本尺寸标注框架.

        Args:
            image: 原始图像

        Returns:
            叠加标注后的图像
        """
        draw = ImageDraw.Draw(image)
        w, h = image.size

        # 底部加总长标注
        margin_bottom = 30

        # 标注样式
        line_color = (100, 100, 100)
        text_color = (80, 80, 80)

        # 底部总长标注线
        y_base = h - margin_bottom
        draw.line([(20, y_base), (w - 20, y_base)], fill=line_color, width=2)

        # 左端标注
        draw.line([(20, y_base - 10), (20, y_base + 10)], fill=line_color, width=2)
        # 右端标注
        draw.line([(w - 20, y_base - 10), (w - 20, y_base + 10)], fill=line_color, width=2)

        # 总长文字
        try:
            draw.text(
                (w // 2 - 40, y_base + 5),
                "L = TOTAL LENGTH",
                fill=text_color,
            )
        except Exception:
            pass

        # 左侧高度标注线
        x_left = 10
        draw.line([(x_left, 20), (x_left, h - 80)], fill=line_color, width=2)

        # 高度标注端点
        draw.line([(x_left - 8, 20), (x_left + 8, 20)], fill=line_color, width=2)
        draw.line(
            [(x_left - 8, h - 80), (x_left + 8, h - 80)], fill=line_color, width=2
        )

        # 高度文字
        try:
            draw.text(
                (x_left + 5, h // 2 - 10),
                "H",
                fill=text_color,
            )
        except Exception:
            pass

        logger.info(f"尺寸标注叠加完成: {w}×{h}")
        return image