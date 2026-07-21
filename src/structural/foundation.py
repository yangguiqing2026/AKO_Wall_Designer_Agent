"""基础设计模块 - 依据 GB 50007-2011."""

import math
from dataclasses import dataclass
from typing import Any

from src.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class FoundationDesign:
    """基础设计结果."""

    type: str
    base_length: int
    base_width: int
    height: int
    embed_depth: int
    reinforcement: str
    soil_pressure: float
    overturning_ratio: float
    sliding_ratio: float


class FoundationDesigner:
    """独立基础设计器 - 设计扶壁柱独立基础.

    依据 GB 50007-2011《建筑地基基础设计规范》。
    验算: 地基承载力、抗倾覆稳定、抗滑移稳定。
    """

    def __init__(self):
        """初始化基础设计器."""
        pass

    def design(
        self,
        vertical_load: float,
        moment: float,
        shear: float,
        soil_capacity: float = 150.0,
        column_width: float = 300.0,
        column_depth: float = 400.0,
    ) -> dict[str, Any]:
        """设计独立基础尺寸与配筋.

        Args:
            vertical_load: 竖向荷载 (kN), 包含柱自重
            moment: 柱底弯矩 (kN·m)
            shear: 柱底剪力 (kN)
            soil_capacity: 地基承载力特征值 (kPa)
            column_width: 柱截面宽度 (mm)
            column_depth: 柱截面深度 (mm)

        Returns:
            基础设计结果字典
        """
        # 估算基底尺寸
        base_size = self._estimate_base_size(
            vertical_load, moment, shear, soil_capacity, column_width, column_depth
        )

        base_length = base_size["length"]
        base_width = base_size["width"]
        base_height = base_size["height"]
        embed_depth = base_size["embed_depth"]

        # 验算地基承载力
        soil_pressure = self._check_bearing_pressure(
            vertical_load, moment, shear, base_length, base_width, base_height, embed_depth
        )

        # 抗倾覆验算
        overturning_ratio = self._check_overturning(
            moment, vertical_load, shear, base_length, base_height, embed_depth
        )

        # 抗滑移验算
        sliding_ratio = self._check_sliding(
            vertical_load, shear, base_length, base_width
        )

        # 配筋
        reinforcement = self._design_reinforcement(base_length, base_width, base_height)

        # 评估
        if soil_pressure > soil_capacity * 1.2:
            logger.warning(
                f"地基承载力不足: {soil_pressure:.1f} > {soil_capacity * 1.2:.1f} kPa"
            )
        if overturning_ratio < 1.5:
            logger.warning(
                f"抗倾覆不满足: K={overturning_ratio:.2f} < 1.5"
            )
        if sliding_ratio < 1.3:
            logger.warning(
                f"抗滑移不满足: K={sliding_ratio:.2f} < 1.3"
            )

        design = FoundationDesign(
            type="独立基础",
            base_length=base_length,
            base_width=base_width,
            height=base_height,
            embed_depth=embed_depth,
            reinforcement=reinforcement,
            soil_pressure=soil_pressure,
            overturning_ratio=overturning_ratio,
            sliding_ratio=sliding_ratio,
        )

        logger.info(
            f"基础设计: {base_length}×{base_width}×{base_height}mm, "
            f"埋深{embed_depth}mm, p={soil_pressure:.1f}kPa, "
            f"Ko={overturning_ratio:.2f}, Ks={sliding_ratio:.2f}"
        )

        return {
            "foundation_type": "独立基础",
            "base_length": base_length,
            "base_width": base_width,
            "height": base_height,
            "embed_depth": embed_depth,
            "reinforcement": reinforcement,
            "soil_pressure": soil_pressure,
            "overturning_ratio": overturning_ratio,
            "sliding_ratio": sliding_ratio,
        }

    def _estimate_base_size(
        self,
        vertical_load: float,
        moment: float,
        shear: float,
        soil_capacity: float,
        column_width: float,
        column_depth: float,
    ) -> dict[str, int]:
        """估算基底尺寸.

        Args:
            vertical_load: 竖向荷载 (kN)
            moment: 弯矩 (kN·m)
            shear: 剪力 (kN)
            soil_capacity: 地基承载力 (kPa)
            column_width: 柱宽 (mm)
            column_depth: 柱深 (mm)

        Returns:
            估算的基底尺寸字典
        """
        # 估算所需基底面积: A = N / (fa - γm * d)
        # 简化: A ≈ N / (0.8 * fa)
        required_area = vertical_load / (0.8 * soil_capacity)  # m²

        # 增加偏心放大系数
        if moment > 0:
            required_area *= 1.3

        # 换算为正方形边长 (mm)
        side = max(600, int(math.sqrt(required_area) * 1000))

        # 向上取整到100mm
        side = ((side + 99) // 100) * 100

        # 最小边长 >= 柱宽+400
        side = max(side, int(column_width + 400))

        # 基础高度
        if moment < 10:
            height = 400
        elif moment < 30:
            height = 500
        elif moment < 60:
            height = 600
        else:
            height = 700

        # 埋深
        embed_depth = 800 if height < 600 else 1000

        return {
            "length": side,
            "width": side,
            "height": height,
            "embed_depth": embed_depth,
        }

    def _check_bearing_pressure(
        self,
        vertical_load: float,
        moment: float,
        shear: float,
        base_length: float,
        base_width: float,
        base_height: float,
        embed_depth: float,
    ) -> float:
        """验算地基承载力.

        Args:
            vertical_load: 竖向荷载 (kN)
            moment: 弯矩 (kN·m)
            shear: 剪力 (kN)
            base_length: 基底长 (mm)
            base_width: 基底宽 (mm)
            base_height: 基础高 (mm)
            embed_depth: 埋深 (mm)

        Returns:
            最大基底压力 (kPa)
        """
        import math

        L = base_length / 1000.0  # m
        B = base_width / 1000.0
        H = base_height / 1000.0
        D = embed_depth / 1000.0

        # 基础自重
        G_footing = L * B * H * 25  # kN
        G_soil = L * B * D * 18  # kN (覆土重)

        N_total = vertical_load + G_footing + G_soil
        M_total = moment + shear * (H + D)

        A = L * B
        W = B * L * L / 6  # 抵抗矩

        # 偏心距
        e = M_total / N_total if N_total > 0 else 0

        if e > L / 6:
            # 基底脱开
            pmax = 2 * N_total / (3 * B * (L / 2 - e))
        else:
            pmax = N_total / A + M_total / W

        return pmax

    def _check_overturning(
        self,
        moment: float,
        vertical_load: float,
        shear: float,
        base_length: float,
        base_height: float,
        embed_depth: float,
    ) -> float:
        """抗倾覆验算.

        Args:
            moment: 倾覆力矩 (kN·m)
            vertical_load: 竖向荷载 (kN)
            shear: 水平力 (kN)
            base_length: 基底长 (mm)
            base_height: 基础高 (mm)
            embed_depth: 埋深 (mm)

        Returns:
            抗倾覆安全系数
        """
        import math

        L = base_length / 1000.0

        # 抗倾覆力矩 (基础自重+覆土)
        G_footing = L * L * (base_height / 1000.0) * 25
        G_soil = L * L * (embed_depth / 1000.0) * 18

        M_resist = (vertical_load + G_footing + G_soil) * L / 2
        M_overturn = moment + shear * (base_height + embed_depth) / 1000.0

        if M_overturn < 0.01:
            return 999.0

        return M_resist / M_overturn

    def _check_sliding(
        self,
        vertical_load: float,
        shear: float,
        base_length: float,
        base_width: float,
    ) -> float:
        """抗滑移验算.

        Args:
            vertical_load: 竖向荷载 (kN)
            shear: 水平力 (kN)
            base_length: 基底长 (mm)
            base_width: 基底宽 (mm)

        Returns:
            抗滑移安全系数
        """
        import math

        # 摩擦系数 (混凝土与土)
        mu = 0.35

        friction = mu * vertical_load
        if shear < 0.01:
            return 999.0

        return friction / shear

    def _design_reinforcement(
        self, base_length: int, base_width: int, base_height: int
    ) -> str:
        """设计基础配筋.

        Args:
            base_length: 基底长 (mm)
            base_width: 基底宽 (mm)
            base_height: 基础高 (mm)

        Returns:
            配筋描述
        """
        if base_height < 500:
            return "Φ12@150 (双向)"
        elif base_height < 700:
            return "Φ14@150 (双向)"
        else:
            return "Φ16@150 (双向)"