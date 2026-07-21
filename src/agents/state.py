"""LangGraph 状态定义模块."""

from enum import Enum
from typing import Any, Optional, TypedDict


class ProcessingStatus(str, Enum):
    """处理状态枚举."""

    PENDING = "pending"
    PARSING = "parsing"
    CALCULATING = "calculating"
    STRUCTURAL_DESIGN = "structural_design"
    GEOMETRY = "geometry"
    SKETCH = "sketch"
    RENDER = "render"
    REPORT = "report"
    COMPLETE = "complete"
    ERROR = "error"


class AgentState(TypedDict, total=False):
    """Agent 全局状态定义.

    字段可选 (total=False) 以支持逐步填充。
    """

    # 输入
    raw_input: str

    # 解析后的设计参数
    parsed_params: Optional[dict[str, Any]]

    # 模数计算结果
    modular_result: Optional[dict[str, Any]]

    # 风荷载计算结果
    wind_load: Optional[dict[str, float]]

    # 柱设计结果
    column_design: Optional[dict[str, Any]]

    # 基础设计结果
    foundation_design: Optional[dict[str, Any]]

    # 输出文件路径
    sketch_path: Optional[str]
    render_path: Optional[str]
    report_path: Optional[str]
    model_path: Optional[str]

    # 材料清单
    material_list: Optional[dict[str, Any]]

    # 状态管理
    status: ProcessingStatus
    error_message: Optional[str]
    progress: float


def create_initial_state(user_input: str) -> AgentState:
    """创建初始状态.

    Args:
        user_input: 用户原始输入

    Returns:
        初始化的 AgentState
    """
    return AgentState(
        raw_input=user_input,
        parsed_params=None,
        modular_result=None,
        wind_load=None,
        column_design=None,
        foundation_design=None,
        sketch_path=None,
        render_path=None,
        report_path=None,
        model_path=None,
        material_list=None,
        status=ProcessingStatus.PENDING,
        error_message=None,
        progress=0.0,
    )