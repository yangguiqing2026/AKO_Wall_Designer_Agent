# ============================================
# Author: AKO_studio
# Agent: AKO_wall_designer_agent
# Generated: 2026-07-30
# ============================================
#
"""材质库模块 - 管理建筑材质定义和LoRA映射."""

from dataclasses import dataclass
from typing import Optional

from src.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class MaterialDefinition:
    """材质定义."""

    name: str
    display_name: str
    category: str  # concrete, steel, coating
    lora_weight_path: str
    lora_scale: float
    color_temperature: str  # neutral, warm, cool
    description: str
    negative_prompt: str


class MaterialLibrary:
    """材质库 - 管理所有可用材质.

    包含混凝土系列、钢柱系列、涂料系列等材质定义。
    """

    MATERIALS: dict[str, MaterialDefinition] = {
        "concrete_fair": MaterialDefinition(
            name="concrete_fair",
            display_name="清水混凝土",
            category="concrete",
            lora_weight_path="models/lora/concrete_fair.safetensors",
            lora_scale=0.8,
            color_temperature="neutral",
            description="光滑表面，自然灰色，有螺栓孔纹理",
            negative_prompt="colorful, painted, rusty, dirty, cracks, damaged",
        ),
        "concrete_wood": MaterialDefinition(
            name="concrete_wood",
            display_name="仿木纹混凝土",
            category="concrete",
            lora_weight_path="models/lora/concrete_wood.safetensors",
            lora_scale=0.7,
            color_temperature="warm",
            description="仿木纹理压印混凝土",
            negative_prompt="painted, steel, metal, smooth, glossy",
        ),
        "concrete_rustic": MaterialDefinition(
            name="concrete_rustic",
            display_name="粗犷混凝土",
            category="concrete",
            lora_weight_path="models/lora/concrete_rustic.safetensors",
            lora_scale=0.75,
            color_temperature="neutral",
            description="粗犷表面质感，可见骨料",
            negative_prompt="smooth, polished, painted, glossy",
        ),
        "steel_fluoro": MaterialDefinition(
            name="steel_fluoro",
            display_name="氟碳喷涂钢柱",
            category="steel",
            lora_weight_path="models/lora/steel_fluoro.safetensors",
            lora_scale=0.7,
            color_temperature="cool",
            description="氟碳喷涂金属表面，可选多种颜色",
            negative_prompt="rusty, concrete, wood, rough, dirty",
        ),
        "steel_corten": MaterialDefinition(
            name="steel_corten",
            display_name="耐候钢锈蚀",
            category="steel",
            lora_weight_path="models/lora/steel_corten.safetensors",
            lora_scale=0.8,
            color_temperature="warm",
            description="耐候钢自然锈蚀效果，红褐色",
            negative_prompt="painted, clean, smooth, new, silver",
        ),
    }

    @classmethod
    def get_material(cls, name: str) -> Optional[MaterialDefinition]:
        """获取材质定义.

        Args:
            name: 材质名称

        Returns:
            MaterialDefinition 或 None
        """
        return cls.MATERIALS.get(name)

    @classmethod
    def get_by_surface_finish(cls, surface_finish: str) -> MaterialDefinition:
        """根据表面效果映射到材质.

        Args:
            surface_finish: 表面效果描述

        Returns:
            对应的 MaterialDefinition
        """
        mapping = {
            "fair-faced": "concrete_fair",
            "fair_faced": "concrete_fair",
            "wood-grain": "concrete_wood",
            "wood_grain": "concrete_wood",
            "wood": "concrete_wood",
            "rustic": "concrete_rustic",
        }
        key = mapping.get(surface_finish, "concrete_fair")
        return cls.MATERIALS[key]

    @classmethod
    def get_by_column_material(cls, column_material: str) -> MaterialDefinition:
        """根据柱材质映射到材质.

        Args:
            column_material: 柱材质 ("concrete", "steel", "steel_corten")

        Returns:
            对应的 MaterialDefinition
        """
        mapping = {
            "concrete": "concrete_fair",
            "steel": "steel_fluoro",
            "steel_corten": "steel_corten",
        }
        key = mapping.get(column_material, "concrete_fair")
        return cls.MATERIALS[key]

    @classmethod
    def list_all(cls) -> list[MaterialDefinition]:
        """列出所有可用材质.

        Returns:
            材质定义列表
        """
        return list(cls.MATERIALS.values())