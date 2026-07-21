"""板排布模块 - 多层高度布局计算."""

import math
from dataclasses import dataclass
from typing import Any


@dataclass
class PanelLayoutResult:
    """板排布结果."""

    total_height_layers: int
    actual_wall_height: float
    is_height_adjusted: bool
    adjustment_message: str


class PanelLayoutCalculator:
    """面板垂直布局计算器 - 计算高度方向的面板层数.

    根据墙高和面板高度，计算需要几层面板，是否调整墙高。
    """

    def calculate(
        self,
        modular_result: dict[str, Any],
        wall_height: float,
        panel_height: float = 2400,
    ) -> dict[str, Any]:
        """计算高度方向排布并更新面板数据.

        Args:
            modular_result: 模数计算结果 (来自 ModularCalculator)
            wall_height: 围墙总高度 (mm)
            panel_height: 标准面板高度 (mm), 默认2400

        Returns:
            排布结果字典
        """
        # 计算层数
        raw_layers = wall_height / panel_height
        num_layers = max(1, round(raw_layers))

        # 实际高度
        actual_height = num_layers * panel_height
        is_adjusted = abs(actual_height - wall_height) > 10

        adjustment = ""
        if is_adjusted:
            if actual_height > wall_height:
                adjustment = (
                    f"墙高从 {wall_height}mm 调整为 {actual_height}mm "
                    f"({num_layers}层×{panel_height}mm)"
                )
            else:
                adjustment = (
                    f"墙高从 {wall_height}mm 调整为 {actual_height}mm "
                    f"({num_layers}层×{panel_height}mm)"
                )

        # 更新所有面板的高度和层索引
        panels = modular_result.get("total_panels", [])
        columns = modular_result.get("columns", [])

        # 为每层复制面板
        all_panels = []
        for layer in range(num_layers):
            for panel_data in panels:
                panel = dict(panel_data)
                panel["height"] = panel_height
                panel["layer_index"] = layer
                panel["position_y"] = layer * panel_height + panel_height / 2
                all_panels.append(panel)

        # 更新柱高度
        for col_data in columns:
            col_data["height"] = actual_height

        return {
            "total_height_layers": num_layers,
            "actual_wall_height": actual_height,
            "is_height_adjusted": is_adjusted,
            "adjustment_message": adjustment,
            "total_panels": all_panels,
            "columns": columns,
        }