# ============================================
# Author: AKO_studio
# Agent: AKO_wall_designer_agent
# Generated: 2026-07-30
# ============================================
#
"""参数解析模块 - LLM Function Calling + Pydantic 校验."""

import json
import os
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field, model_validator

from src.parsers.prompt_templates import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE
from src.utils.logging import get_logger

logger = get_logger(__name__)


class ColumnMaterial(str, Enum):
    """扶壁柱材质枚举."""

    CONCRETE = "concrete"
    STEEL = "steel"
    STEEL_CORTEN = "steel_corten"


class TerrainCategory(str, Enum):
    """地面粗糙度类别枚举."""

    A = "A"  # 近海海面、海岛、海岸
    B = "B"  # 田野、乡村、丘陵
    C = "C"  # 有密集建筑群的城市市区
    D = "D"  # 有密集建筑群且房屋较高的城市市区


class DesignInput(BaseModel):
    """设计输入参数模型 - Pydantic 校验."""

    wall_length: float = Field(50000, ge=0, description="围墙总长度(mm)")
    wall_height: float = Field(2400, ge=0, description="围墙总高度(mm)")
    column_spacing: float = Field(3600, ge=0, description="扶壁柱间距(mm)")
    column_material: ColumnMaterial = Field(
        ColumnMaterial.CONCRETE, description="扶壁柱材质"
    )
    panel_width: float = Field(600, ge=300, le=1200, description="墙板宽度(mm)")
    panel_height: float = Field(2400, ge=1200, le=3600, description="墙板高度(mm)")
    column_width: Optional[float] = Field(None, description="柱宽(mm)，不填则自动计算")
    wind_pressure: Optional[float] = Field(None, description="基本风压(kN/m²)")
    terrain_category: TerrainCategory = Field(
        TerrainCategory.C, description="地面粗糙度"
    )
    surface_finish: str = Field("fair-faced", description="表面效果")
    seismic_intensity: int = Field(6, ge=6, le=9, description="抗震设防烈度")

    @model_validator(mode="after")
    def set_defaults_and_fix_zeros(self):
        """修正 LLM 返回的 0 值，设置合理的默认值."""
        # 如果 wall_length 为 0，设为默认 50000 (LLM 未提供时的回退)
        if self.wall_length == 0:
            self.wall_length = 50000.0
        if self.wall_length < 0:
            raise ValueError("wall_length 不能为负值")
        # 如果 wall_height 为 0，设为默认 2400
        if self.wall_height == 0:
            self.wall_height = 2400.0
        if self.wall_height < 0:
            raise ValueError("wall_height 不能为负值")
        # 如果 column_spacing 为 0，设为默认 3600
        if self.column_spacing == 0:
            self.column_spacing = 3600.0
        if self.column_spacing < 0:
            raise ValueError("column_spacing 不能为负值")

        # 当柱宽未填写时，根据材质自动设置默认值
        if self.column_width is None or self.column_width == 0:
            if self.column_material and self.column_material.value == "concrete":
                self.column_width = 300.0
            else:
                self.column_width = 250.0

        return self


class ParameterParser:
    """参数解析器 - 将自然语言转换为结构化设计参数.

    支持两种模式:
    1. LLM模式: 调用 OpenAI/Anthropic API 进行语义解析
    2. 本地模式: 基于规则的关键词提取 (无API时的降级方案)
    """

    def __init__(self, use_llm: bool = True, config: Any | None = None):
        """初始化解析器.

        Args:
            use_llm: 是否使用 LLM API，False 则使用本地规则解析
            config: Config 实例，用于获取 LLM 配置 (可选)
        """
        self.use_llm = use_llm
        self.config = config
        # 自动获取 LLM 配置 (优先 Qwen > OpenAI)
        if config:
            llm_cfg = config.get_llm_config()
            self.api_key = llm_cfg.get("api_key")
            self.api_base = llm_cfg.get("api_base")
            self.model = llm_cfg.get("model", "qwen-plus")
        else:
            self.api_key = os.getenv("QWEN_API_KEY") or os.getenv("OPENAI_API_KEY")
            self.api_base = os.getenv("QWEN_API_BASE")
            self.model = os.getenv("QWEN_MODEL", "qwen-plus") if os.getenv("QWEN_API_KEY") else "gpt-4o"

    async def parse(self, raw_input: str) -> dict[str, Any]:
        """解析用户输入为结构化设计参数.

        Args:
            raw_input: 用户自然语言输入

        Returns:
            验证后的设计参数字典
        """
        if self.use_llm and self.api_key:
            result = await self._parse_with_llm(raw_input)
        else:
            result = self._parse_with_rules(raw_input)

        # Pydantic 校验
        validated = DesignInput(**result)
        return validated.model_dump()

    async def _parse_with_llm(self, raw_input: str) -> dict[str, Any]:
        """使用 LLM (Qwen / OpenAI) 解析参数.

        通过 OpenAI 兼容 SDK 调用，支持:
        - Qwen (通义千问): DashScope API, OpenAI 兼容
        - OpenAI: GPT-4o 等

        Args:
            raw_input: 用户原始输入

        Returns:
            解析后的参数字典
        """
        try:
            from openai import AsyncOpenAI

            # 构建客户端 (Qwen API 需要 base_url)
            if self.api_base:
                client = AsyncOpenAI(
                    api_key=self.api_key,
                    base_url=self.api_base,
                )
            else:
                client = AsyncOpenAI(api_key=self.api_key)

            user_prompt = USER_PROMPT_TEMPLATE.format(raw_input=raw_input)

            # Qwen 的 json_object response_format 支持
            response = await client.chat.completions.create(
                model=self.model or "qwen-plus",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.1,
                max_tokens=500,
                response_format={"type": "json_object"},
            )

            content = response.choices[0].message.content or "{}"
            result = json.loads(content)
            logger.info(f"LLM ({self.model}) 解析成功: {result}")
            return result

        except Exception as e:
            logger.warning(f"LLM 解析失败 ({self.model})，降级到规则解析: {e}")
            return self._parse_with_rules(raw_input)

    def _parse_with_rules(self, raw_input: str) -> dict[str, Any]:
        """基于规则的关键词提取 (降级方案).

        Args:
            raw_input: 用户原始输入

        Returns:
            解析后的参数字典
        """
        import re

        text = raw_input.lower()
        result: dict[str, Any] = {
            "wall_length": 10000,
            "wall_height": 2400,
            "column_spacing": 3600,
            "column_material": "concrete",
            "panel_width": 600,
            "panel_height": 2400,
            "column_width": None,
            "wind_pressure": None,
            "terrain_category": "C",
            "surface_finish": "fair-faced",
            "seismic_intensity": 6,
        }

        # 提取长度: 匹配模式 "XX米长"/"XX米围墙"/"XX米" (开头数字+米)
        length_match = re.search(r"(\d+\.?\d*)\s*米\s*(?:长|围墙|钢柱|的)", raw_input)
        if length_match:
            result["wall_length"] = float(length_match.group(1)) * 1000
        else:
            # 匹配开头出现的数字+米 (如 "100米钢柱围墙" 中的 100米)
            first_meter = re.search(r"^\D*(\d+)\s*米", raw_input)
            if first_meter:
                result["wall_length"] = float(first_meter.group(1)) * 1000

        # 提取长度 (mm 表示)
        length_mm = re.search(r"总?长\s*(\d+)\s*(?:mm|毫米)", raw_input)
        if length_mm:
            result["wall_length"] = float(length_mm.group(1))

        # 提取高度: 匹配 "高X米"/"高X.X米"/"X米高"/"高度X"
        height_match = re.search(r"高\s*(\d+\.?\d*)\s*米", raw_input)
        if height_match:
            result["wall_height"] = float(height_match.group(1)) * 1000
        else:
            height_match = re.search(r"(\d+\.?\d*)\s*米\s*高|高度\s*(\d+\.?\d*)", raw_input)
            if height_match:
                val = height_match.group(1) or height_match.group(2)
                result["wall_height"] = float(val) * 1000

        height_mm = re.search(r"高\s*(\d+)\s*(?:mm|毫米)", raw_input)
        if height_mm:
            result["wall_height"] = float(height_mm.group(1))

        # 提取柱间距
        spacing_match = re.search(
            r"柱[间]?距\s*(\d+\.?\d*)\s*米|间距\s*(\d+)\s*(?:mm)?", raw_input
        )
        if spacing_match:
            val = spacing_match.group(1) or spacing_match.group(2)
            result["column_spacing"] = float(val) * (
                1000 if spacing_match.group(1) else 1
            )

        # 提取材质
        if any(w in text for w in ["钢", "steel", "q355"]):
            if any(w in text for w in ["耐候", "corten", "锈"]):
                result["column_material"] = "steel_corten"
            else:
                result["column_material"] = "steel"
        else:
            result["column_material"] = "concrete"

        # 提取面板宽度
        panel_w = re.search(r"板宽\s*(\d+)|墙板\s*(\d+)\s*mm", raw_input)
        if panel_w:
            result["panel_width"] = float(panel_w.group(1) or panel_w.group(2))

        # 提取风压
        wind_match = re.search(r"风[压荷].*?(\d+\.?\d*)", raw_input)
        if wind_match:
            result["wind_pressure"] = float(wind_match.group(1))

        # 提取抗震烈度
        seismic_match = re.search(r"(\d)\s*度", raw_input)
        if seismic_match:
            val = int(seismic_match.group(1))
            if 6 <= val <= 9:
                result["seismic_intensity"] = val

        # 提取表面效果
        if any(w in text for w in ["木纹", "wood"]):
            result["surface_finish"] = "wood-grain"
        elif any(w in text for w in ["粗犷", "rustic"]):
            result["surface_finish"] = "rustic"
        else:
            result["surface_finish"] = "fair-faced"

        # 提取地面粗糙度
        if any(w in text for w in ["a类", "近海", "海岛", "海岸"]):
            result["terrain_category"] = "A"
        elif any(w in text for w in ["b类", "田野", "乡村", "丘陵"]):
            result["terrain_category"] = "B"
        elif any(w in text for w in ["d类", "高密集"]):
            result["terrain_category"] = "D"

        logger.info(f"规则解析完成: {result}")
        return result