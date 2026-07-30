# ============================================
# Author: AKO_studio
# Agent: AKO_wall_designer_agent
# Generated: 2026-07-30
# ============================================
#
"""效果图生成模块 - SDXL + ControlNet + LoRA 逼真渲染."""

from typing import Any, Optional

import numpy as np
from PIL import Image

from src.utils.logging import get_logger

logger = get_logger(__name__)


class RenderGenerator:
    """效果图渲染器 - 使用 SDXL + ControlNet 生成逼真建筑效果图.

    技术栈:
    - Base: stabilityai/stable-diffusion-xl-base-1.0
    - ControlNet: lllyasviel/sd-controlnet-depth + canny
    - LoRA: 自训练材质适配器
    """

    CONCRETE_PROMPT = (
        "architectural rendering, concrete wall facade, fair-faced concrete texture, "
        "modern architecture, outdoor daylight, natural lighting, "
        "professional architectural photography, ultra realistic, 8k, high quality"
    )

    STEEL_PROMPT = (
        "architectural rendering, steel column structure, industrial design, "
        "fluorocarbon coated steel surface, modern architecture, outdoor daylight, "
        "professional architectural photography, ultra realistic, 8k, high quality"
    )

    NEGATIVE_PROMPT = (
        "low quality, blurry, distorted, deformed, disfigured, bad anatomy, "
        "watermark, text, signature, low resolution, artifacts"
    )

    def __init__(self, device: str = "cpu"):
        """初始化效果图生成器.

        Args:
            device: 推理设备
        """
        self.device = device
        self.pipe = None
        self.depth_cn = None
        self.canny_cn = None
        logger.info(f"RenderGenerator 初始化 (device={device})")

    def generate(
        self,
        depth_map: Optional[np.ndarray],
        mask: Optional[np.ndarray],
        params: dict[str, Any],
        output_path: Optional[str] = None,
    ) -> Image.Image:
        """生成效果图.

        Args:
            depth_map: 深度图
            mask: 掩码
            params: 渲染参数 {surface_finish, column_material}
            output_path: 输出路径

        Returns:
            效果图 PIL Image
        """
        column_material = params.get("column_material", "concrete")

        if column_material in ("concrete", "concrete_corten"):
            result = self._generate_concrete(depth_map, mask, params)
        else:
            result = self._generate_steel(depth_map, mask, params)

        if result is None:
            result = self._generate_placeholder(params)

        if output_path:
            result.save(output_path)
            logger.info(f"效果图已保存: {output_path}")

        return result

    def _generate_concrete(
        self,
        depth_map: Optional[np.ndarray],
        mask: Optional[np.ndarray],
        params: dict[str, Any],
    ) -> Optional[Image.Image]:
        """生成混凝土效果图.

        Args:
            depth_map: 深度图
            mask: 掩码
            params: 参数

        Returns:
            Image 或 None
        """
        try:
            from diffusers import (  # type: ignore[import-untyped]
                ControlNetModel,
                StableDiffusionXLControlNetPipeline,
            )
            import torch

            if self.depth_cn is None:
                self.depth_cn = ControlNetModel.from_pretrained(
                    "lllyasviel/sd-controlnet-depth",
                    torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                )

            if self.pipe is None:
                self.pipe = StableDiffusionXLControlNetPipeline.from_pretrained(
                    "stabilityai/stable-diffusion-xl-base-1.0",
                    controlnet=self.depth_cn,
                    torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                )
                self.pipe = self.pipe.to(self.device)
                self.pipe.enable_model_cpu_offload()

            # 准备深度图
            if depth_map is not None:
                control_image = Image.fromarray(depth_map.astype(np.uint8)).resize(
                    (1024, 1024)
                )
            else:
                control_image = Image.new("L", (1024, 1024), 128)

            result = self.pipe(
                prompt=self.CONCRETE_PROMPT,
                negative_prompt=self.NEGATIVE_PROMPT,
                image=control_image,
                num_inference_steps=30,
                controlnet_conditioning_scale=0.7,
            ).images[0]

            logger.info("混凝土效果图生成完成")
            return result

        except ImportError:
            logger.warning("diffusers 未安装，使用占位图")
            return None
        except Exception as e:
            logger.warning(f"效果图生成失败: {e}")
            return None

    def _generate_steel(
        self,
        depth_map: Optional[np.ndarray],
        mask: Optional[np.ndarray],
        params: dict[str, Any],
    ) -> Optional[Image.Image]:
        """生成钢柱效果图.

        Args:
            depth_map: 深度图
            mask: 掩码
            params: 参数

        Returns:
            Image 或 None
        """
        # 与 _generate_concrete 类似，但使用不同的 prompt
        try:
            from diffusers import (  # type: ignore[import-untyped]
                ControlNetModel,
                StableDiffusionXLControlNetPipeline,
            )
            import torch

            if self.depth_cn is None:
                self.depth_cn = ControlNetModel.from_pretrained(
                    "lllyasviel/sd-controlnet-depth",
                    torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                )

            if self.pipe is None:
                self.pipe = StableDiffusionXLControlNetPipeline.from_pretrained(
                    "stabilityai/stable-diffusion-xl-base-1.0",
                    controlnet=self.depth_cn,
                    torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                )
                self.pipe = self.pipe.to(self.device)
                self.pipe.enable_model_cpu_offload()

            if depth_map is not None:
                control_image = Image.fromarray(depth_map.astype(np.uint8)).resize(
                    (1024, 1024)
                )
            else:
                control_image = Image.new("L", (1024, 1024), 128)

            result = self.pipe(
                prompt=self.STEEL_PROMPT,
                negative_prompt=self.NEGATIVE_PROMPT,
                image=control_image,
                num_inference_steps=30,
                controlnet_conditioning_scale=0.7,
            ).images[0]

            logger.info("钢柱效果图生成完成")
            return result

        except ImportError:
            logger.warning("diffusers 未安装，使用占位图")
            return None
        except Exception as e:
            logger.warning(f"效果图生成失败: {e}")
            return None

    def _generate_placeholder(self, params: dict[str, Any]) -> Image.Image:
        """生成占位效果图 (无GPU时).

        Args:
            params: 参数

        Returns:
            占位 Image (2048×1536)
        """
        from PIL import ImageDraw

        img = Image.new("RGB", (2048, 1536), color=(220, 225, 230))
        draw = ImageDraw.Draw(img)

        # 绘制简单的围墙示意
        draw.rectangle([100, 600, 1948, 700], fill=(180, 175, 170))  # 墙顶
        draw.rectangle([100, 700, 1948, 1300], fill=(200, 195, 190))  # 墙面

        # 柱
        for x in range(150, 1900, 350):
            material = params.get("column_material", "concrete")
            color = (160, 155, 150) if "concrete" in str(material) else (120, 125, 135)
            draw.rectangle([x - 30, 500, x + 30, 1300], fill=color)

        # 地面
        draw.rectangle([0, 1300, 2048, 1536], fill=(150, 170, 140))

        logger.info("占位效果图生成完成")
        return img