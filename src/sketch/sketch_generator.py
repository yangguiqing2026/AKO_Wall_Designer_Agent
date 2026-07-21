"""草图生成模块 - ControlNet + SD 手绘风格线稿生成."""

from typing import Optional

from PIL import Image

from src.utils.logging import get_logger

logger = get_logger(__name__)


class SketchGenerator:
    """草图生成器 - 使用 ControlNet-Lineart 将线稿转化为手绘风格草图.

    技术栈:
    - ControlNet: lllyasviel/sd-controlnet-lineart
    - Base Model: runwayml/stable-diffusion-v1-5
    """

    SKETCH_PROMPT = (
        "architectural sketch, hand-drawn pencil style, white background, "
        "clean linework, technical drawing, no color, no shading, "
        "architectural elevation drawing, blueprint style"
    )

    SKETCH_NEGATIVE = (
        "photorealistic, color, texture, shading, blurry, messy, "
        "render, 3d, photograph, painting, digital art"
    )

    def __init__(self, device: str = "cpu"):
        """初始化草图生成器.

        Args:
            device: 推理设备 ("cuda" 或 "cpu")
        """
        self.device = device
        self.pipe = None
        self.controlnet = None
        logger.info(f"SketchGenerator 初始化 (device={device})")

    def generate_from_lineart(
        self,
        lineart_image: Image.Image,
        output_path: Optional[str] = None,
        with_dimensions: bool = True,
    ) -> Image.Image:
        """从线稿生成手绘风格草图.

        Args:
            lineart_image: 输入的线稿图像
            output_path: 输出路径, None 则不保存
            with_dimensions: 是否叠加尺寸标注

        Returns:
            手绘风格草图 PIL Image
        """
        # 首先尝试使用 ControlNet + SD 生成
        result = self._generate_with_ml(lineart_image)

        if result is None:
            # ML 不可用时，使用图像处理模拟手绘效果
            result = self._generate_with_image_processing(lineart_image)

        # 叠加尺寸标注
        if with_dimensions:
            result = self._overlay_dimensions(result)

        # 保存
        if output_path:
            result.save(output_path)
            logger.info(f"草图已保存: {output_path}")

        return result

    def _generate_with_ml(self, lineart_image: Image.Image) -> Optional[Image.Image]:
        """使用 ML 模型生成草图.

        Args:
            lineart_image: 输入线稿

        Returns:
            生成的图像, 如果模型不可用返回 None
        """
        try:
            from diffusers import (  # type: ignore[import-untyped]
                ControlNetModel,
                StableDiffusionControlNetPipeline,
            )
            import torch

            if self.controlnet is None:
                self.controlnet = ControlNetModel.from_pretrained(
                    "lllyasviel/sd-controlnet-lineart",
                    torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                )

            if self.pipe is None:
                self.pipe = StableDiffusionControlNetPipeline.from_pretrained(
                    "runwayml/stable-diffusion-v1-5",
                    controlnet=self.controlnet,
                    torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                )
                self.pipe = self.pipe.to(self.device)
                self.pipe.enable_attention_slicing()

            result = self.pipe(
                prompt=self.SKETCH_PROMPT,
                negative_prompt=self.SKETCH_NEGATIVE,
                image=lineart_image,
                num_inference_steps=30,
                controlnet_conditioning_scale=0.8,
            ).images[0]

            logger.info("ML 草图生成完成")
            return result

        except ImportError:
            logger.warning("diffusers 未安装，使用图像处理模式")
            return None
        except Exception as e:
            logger.warning(f"ML 草图生成失败: {e}")
            return None

    def _generate_with_image_processing(
        self, lineart_image: Image.Image
    ) -> Image.Image:
        """使用图像处理模拟手绘效果.

        Args:
            lineart_image: 输入线稿

        Returns:
            处理后的图像
        """
        import numpy as np
        from PIL import ImageFilter, ImageOps

        # 转为灰度
        gray = lineart_image.convert("L")

        # 反转 (白底黑线 → 浅灰底深灰线)
        gray = ImageOps.invert(gray)

        # 添加模糊模拟手绘
        gray = gray.filter(ImageFilter.GaussianBlur(radius=1))

        # 增强对比
        gray = ImageOps.autocontrast(gray)

        # 轻微旋转模拟手绘不完美
        # gray = gray.rotate(0.3, expand=False, fillcolor=245)

        result = gray.convert("RGB")
        logger.info("图像处理草图生成完成")
        return result

    def _overlay_dimensions(self, image: Image.Image) -> Image.Image:
        """叠加尺寸标注.

        Args:
            image: 原始草图

        Returns:
            叠加尺寸后的图像
        """
        from src.sketch.dimension_overlay import DimensionOverlay

        overlay = DimensionOverlay()
        return overlay.add_dimensions(image)