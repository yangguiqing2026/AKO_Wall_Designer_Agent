"""配置管理模块 - 从环境变量加载配置."""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv


@dataclass
class Config:
    """应用全局配置."""

    # LLM - 支持 OpenAI / Qwen (通义千问) 及兼容 API
    openai_api_key: Optional[str] = None
    qwen_api_key: Optional[str] = None
    qwen_api_base: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    qwen_model: str = "qwen-plus"
    llm_provider: str = "qwen"  # "openai" | "qwen" | "auto"

    # 路径
    model_path: Path = field(default_factory=lambda: Path("./models"))
    output_path: Path = field(default_factory=lambda: Path("./outputs"))

    # 服务器
    host: str = "0.0.0.0"
    port: int = 7860

    # 日志
    log_level: str = "INFO"

    # GPU
    cuda_visible_devices: str = "0"

    # 默认设计参数
    default_panel_width: int = 600
    default_panel_height: int = 2400
    default_terrain_category: str = "C"
    default_seismic_intensity: int = 6
    default_surface_finish: str = "fair-faced"

    # 结构设计默认值
    concrete_grade: str = "C30"
    steel_grade_rebar: str = "HRB400"
    steel_grade_structural: str = "Q355B"
    soil_bearing_capacity: float = 150.0  # kPa

    # 图像生成
    sketch_width: int = 1024
    sketch_height: int = 768
    render_width: int = 2048
    render_height: int = 1536
    num_inference_steps: int = 30
    controlnet_conditioning_scale: float = 0.8
    lora_scale: float = 0.8

    def __post_init__(self):
        """确保路径为 Path 对象."""
        self.model_path = Path(self.model_path)
        self.output_path = Path(self.output_path)

    @classmethod
    def from_env(cls, env_file: Optional[str] = None) -> "Config":
        """从环境变量加载配置.

        Args:
            env_file: .env 文件路径，默认查找当前目录的 .env

        Returns:
            Config 实例
        """
        if env_file:
            load_dotenv(env_file)
        else:
            load_dotenv()

        return cls(
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            qwen_api_key=os.getenv("QWEN_API_KEY"),
            qwen_api_base=os.getenv("QWEN_API_BASE", "https://dashscope.aliyuncs.com/compatible-mode/v1"),
            qwen_model=os.getenv("QWEN_MODEL", "qwen-plus"),
            llm_provider=os.getenv("LLM_PROVIDER", "qwen"),
            model_path=os.getenv("MODEL_PATH", "./models"),
            output_path=os.getenv("OUTPUT_PATH", "./outputs"),
            host=os.getenv("HOST", "0.0.0.0"),
            port=int(os.getenv("PORT", "7860")),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            cuda_visible_devices=os.getenv("CUDA_VISIBLE_DEVICES", "0"),
        )

    def get_llm_config(self) -> dict[str, Optional[str]]:
        """获取当前可用的 LLM API 配置.

        优先级: QWEN_API_KEY > OPENAI_API_KEY > None (降级规则模式)

        Returns:
            {"api_key": ..., "api_base": ..., "model": ..., "provider": ...}
        """
        if self.qwen_api_key:
            return {
                "api_key": self.qwen_api_key,
                "api_base": self.qwen_api_base,
                "model": self.qwen_model,
                "provider": "qwen",
            }
        if self.openai_api_key:
            return {
                "api_key": self.openai_api_key,
                "api_base": None,
                "model": "gpt-4o",
                "provider": "openai",
            }
        return {"api_key": None, "api_base": None, "model": None, "provider": None}

    def ensure_output_dirs(self) -> None:
        """确保输出目录结构存在."""
        (self.output_path / "sketches").mkdir(parents=True, exist_ok=True)
        (self.output_path / "renders").mkdir(parents=True, exist_ok=True)
        (self.output_path / "reports").mkdir(parents=True, exist_ok=True)
        (self.output_path / "models").mkdir(parents=True, exist_ok=True)