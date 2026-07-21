"""模数计算模块 - 基于600mm模数的墙板排布与柱位优化."""

import math
from dataclasses import dataclass
from typing import Any, List

from src.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class Panel:
    """单个墙板."""

    width: float
    height: float
    is_standard: bool
    position_x: float
    position_y: float
    layer_index: int


@dataclass
class Column:
    """单个扶壁柱."""

    width: float
    depth: float
    height: float
    position_x: float
    material: str
    index: int


@dataclass
class ModularResult:
    """模数计算结果."""

    panels_per_span: int
    actual_spacing: float
    num_spans: int
    total_panels: List[Panel]
    columns: List[Column]
    remainder: float
    non_standard_panel_count: int
    adjustment_message: str


class ModularCalculator:
    """模数计算器 - 基于600mm模数计算墙板排布和柱位.

    处理策略:
    - 面板宽度 = 最小600mm，柱间距 = n × panel_width + column_width
    - 剩余长度 < 300mm: 并入相邻段，微调相邻柱距
    - 剩余长度 300~1200mm: 生成非标板，居中或端部放置
    - 剩余长度 > 1200mm: 建议用户调整总长度或柱距
    """

    STANDARD_PANEL_WIDTH: float = 600.0
    DEFAULT_COLUMN_DEPTH: float = 400.0

    def calculate(
        self,
        wall_length: float,
        column_spacing: float,
        panel_width: float = 600.0,
        column_width: float = 300.0,
        column_material: str = "concrete",
    ) -> dict[str, Any]:
        """计算墙板排布方案.

        Args:
            wall_length: 围墙总长度 (mm)
            column_spacing: 柱间距 (mm)
            panel_width: 标准板宽 (mm), 默认600
            column_width: 柱宽 (mm)
            column_material: 柱材质

        Returns:
            模数计算结果字典
        """
        logger.info(
            f"模数计算: length={wall_length}, spacing={column_spacing}, "
            f"panel={panel_width}, col_width={column_width}"
        )

        # 计算有效净距 (减去一个柱宽，因为两端半柱)
        effective_length = wall_length - column_width

        # 计算跨数 = 总长 / 柱间距
        raw_spans = effective_length / column_spacing
        num_spans = round(raw_spans)

        if num_spans < 1:
            num_spans = 1

        # 实际柱间距
        actual_spacing = effective_length / num_spans

        # 每跨面板数
        clear_span = actual_spacing - column_width
        panels_per_span = int(clear_span / panel_width)

        # 剩余长度
        remainder = clear_span - panels_per_span * panel_width

        # 生成面板
        total_panels: list[Panel] = []
        non_standard_count = 0
        column_depth = self.DEFAULT_COLUMN_DEPTH

        current_x = column_width / 2  # 从半个柱宽开始

        for span in range(num_spans):
            span_start = current_x

            for p in range(panels_per_span):
                panel_x = span_start + p * panel_width + panel_width / 2
                total_panels.append(
                    Panel(
                        width=panel_width,
                        height=2400,  # 暂时默认, 布局时更新
                        is_standard=True,
                        position_x=panel_x,
                        position_y=0,
                        layer_index=0,
                    )
                )

            # 处理每跨的余量
            if remainder > 0 and remainder < 300:
                # 微调最后一块板
                if total_panels:
                    total_panels[-1].width += remainder
                    total_panels[-1].is_standard = False
                    non_standard_count += 1
            elif remainder >= 300:
                # 生成非标板
                panel_x = span_start + panels_per_span * panel_width + remainder / 2
                total_panels.append(
                    Panel(
                        width=remainder,
                        height=2400,
                        is_standard=False,
                        position_x=panel_x,
                        position_y=0,
                        layer_index=0,
                    )
                )
                non_standard_count += 1

            current_x = span_start + actual_spacing

        # 生成柱
        columns: list[Column] = []
        col_x = column_width / 2
        for i in range(num_spans + 1):
            columns.append(
                Column(
                    width=column_width,
                    depth=column_depth,
                    height=2400,
                    position_x=col_x,
                    material=column_material,
                    index=i,
                )
            )
            col_x += actual_spacing

        # 调整信息
        final_remainder = effective_length - num_spans * actual_spacing
        adjustment = ""
        if abs(final_remainder) > 1:
            if abs(final_remainder) > 1200:
                adjustment = (
                    f"剩余长度 {final_remainder:.0f}mm > 1200mm，"
                    f"建议调整总长度或柱距"
                )
            else:
                adjustment = (
                    f"实际柱间距调整为 {actual_spacing:.0f}mm, "
                    f"非标段 {final_remainder:.0f}mm"
                )

        result = ModularResult(
            panels_per_span=panels_per_span,
            actual_spacing=actual_spacing,
            num_spans=num_spans,
            total_panels=total_panels,
            columns=columns,
            remainder=final_remainder,
            non_standard_panel_count=non_standard_count,
            adjustment_message=adjustment,
        )

        logger.info(
            f"模数计算完成: {num_spans}跨, {panels_per_span}板/跨, "
            f"总{len(total_panels)}板, {len(columns)}柱, "
            f"非标{non_standard_count}板"
        )

        return {
            "panels_per_span": panels_per_span,
            "actual_spacing": actual_spacing,
            "num_spans": num_spans,
            "total_panels": [
                {
                    "width": p.width,
                    "height": p.height,
                    "is_standard": p.is_standard,
                    "position_x": p.position_x,
                    "position_y": p.position_y,
                    "layer_index": p.layer_index,
                }
                for p in total_panels
            ],
            "columns": [
                {
                    "width": c.width,
                    "depth": c.depth,
                    "height": c.height,
                    "position_x": c.position_x,
                    "material": c.material,
                    "index": c.index,
                }
                for c in columns
            ],
            "remainder": final_remainder,
            "non_standard_panel_count": non_standard_count,
            "adjustment_message": adjustment,
        }