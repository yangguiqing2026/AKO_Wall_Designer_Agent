# ============================================
# Author: AKO_studio
# Agent: AKO_wall_designer_agent
# Generated: 2026-07-30
# ============================================
#
"""LoRA 加载器模块 - 管理 LoRA 权重的加载和卸载."""

import os
from pathlib import Path
from typing import Any, Optional

from src.utils.logging import get_logger

logger = get_logger(__name__)


class LoRALoader:
    """LoRA 权重加载器 - 管理扩散模型的 LoRA 适配器.

    支持 safetensors 格式的 LoRA 权重加载。
    """

    def __init__(self, model_path: Path | str = "./models/lora"):
        """初始化加载器.

        Args:
            model_path: LoRA 模型存储路径
        """
        self.model_path = Path(model_path)
        self.loaded_loras: dict[str, Any] = {}
        logger.info(f"LoRA 加载器初始化: {self.model_path}")

    def load(self, lora_name: str) -> Optional[Any]:
        """加载指定的 LoRA 权重.

        Args:
            lora_name: LoRA 名称 (不含路径前缀)

        Returns:
            LoRA 状态字典，或 None 如果加载失败
        """
        if lora_name in self.loaded_loras:
            logger.debug(f"LoRA 已加载: {lora_name}")
            return self.loaded_loras[lora_name]

        lora_path = self.model_path / f"{lora_name}.safetensors"

        if not lora_path.exists():
            logger.warning(f"LoRA 文件不存在: {lora_path}")
            return None

        try:
            from safetensors.torch import load_file

            state_dict = load_file(str(lora_path))
            self.loaded_loras[lora_name] = state_dict
            logger.info(f"LoRA 加载成功: {lora_name}")
            return state_dict

        except ImportError:
            logger.warning(
                "safetensors 库未安装，无法加载 LoRA 权重"
            )
            return None
        except Exception as e:
            logger.error(f"LoRA 加载失败: {lora_name}, {e}")
            return None

    def unload(self, lora_name: str) -> None:
        """卸载 LoRA 权重释放内存.

        Args:
            lora_name: LoRA 名称
        """
        if lora_name in self.loaded_loras:
            del self.loaded_loras[lora_name]
            logger.info(f"LoRA 已卸载: {lora_name}")

    def unload_all(self) -> None:
        """卸载所有已加载的 LoRA 权重."""
        count = len(self.loaded_loras)
        self.loaded_loras.clear()
        logger.info(f"已卸载全部 {count} 个 LoRA")

    def list_available(self) -> list[str]:
        """列出所有可用的 LoRA 文件.

        Returns:
            LoRA 文件名列表 (不含扩展名)
        """
        if not self.model_path.exists():
            return []

        loraz: list[str] = []
        for f in self.model_path.glob("*.safetensors"):
            loraz.append(f.stem)

        return loraz

    def get_state_dict(self, lora_name: str) -> Optional[dict[str, Any]]:
        """获取已加载的 LoRA 状态字典.

        Args:
            lora_name: LoRA 名称

        Returns:
            状态字典或 None
        """
        return self.loaded_loras.get(lora_name)