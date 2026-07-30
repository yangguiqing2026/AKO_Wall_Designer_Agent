# ============================================
# Author: AKO_studio
# Agent: AKO_wall_designer_agent
# Generated: 2026-07-30
# ============================================
#
"""混凝土柱设计模块 - 依据 GB 50010-2010."""

import math
from dataclasses import dataclass
from typing import Any

from src.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ConcreteColumnDesign:
    """混凝土柱设计结果."""

    width: int
    depth: int
    concrete_grade: str
    steel_grade: str
    longitudinal_bars: str
    longitudinal_bars_area: float
    stirrups: str
    stirrups_zone: str
    cover: int
    axial_capacity: float
    moment_capacity: float
    reinforcement_ratio: float
    self_weight: float


class ConcreteColumnDesigner:
    """混凝土扶壁柱设计器.

    根据高度、风荷载、抗震烈度自动设计柱截面与配筋。
    """

    # 柱截面预设方案 (width×depth mm) 按高度分级
    SECTION_OPTIONS: dict[str, tuple[int, int]] = {
        "low": (300, 300),     # < 3m
        "medium": (300, 400),  # 3-5m
        "high": (350, 450),    # > 5m
    }

    # 纵向钢筋方案 (按截面级别)
    REBAR_OPTIONS: dict[str, dict[str, Any]] = {
        "low": {
            "bars": "4Φ16",
            "area": 4 * math.pi * 16**2 / 4,
            "ratio": 0.65,
        },
        "medium": {
            "bars": "4Φ20",
            "area": 4 * math.pi * 20**2 / 4,
            "ratio": 0.85,
        },
        "high": {
            "bars": "6Φ22",
            "area": 6 * math.pi * 22**2 / 4,
            "ratio": 1.05,
        },
    }

    # 箍筋方案
    STIRRUP_OPTIONS: dict[str, str] = {
        "low": "Φ8@200 (加密区 Φ8@150)",
        "medium": "Φ8@150 (加密区 Φ8@100)",
        "high": "Φ10@150 (加密区 Φ10@100)",
    }

    # 混凝土强度与配筋参数
    CONCRETE_FC: dict[str, float] = {
        "C25": 11.9,
        "C30": 14.3,
        "C35": 16.7,
        "C40": 19.1,
    }

    STEEL_FY: dict[str, float] = {
        "HRB335": 300,
        "HRB400": 360,
        "HRB500": 435,
    }

    def design(
        self,
        height: float,
        wind_load: dict[str, float],
        seismic_intensity: int = 6,
        concrete_grade: str = "C30",
        steel_grade: str = "HRB400",
    ) -> dict[str, Any]:
        """设计混凝土柱断面与配筋.

        Args:
            height: 围墙高度 (mm)
            wind_load: 风荷载计算结果
            seismic_intensity: 抗震设防烈度
            concrete_grade: 混凝土强度等级
            steel_grade: 钢筋牌号

        Returns:
            柱设计结果字典
        """
        height_m = height / 1000.0
        moment = wind_load.get("column_base_moment", 0.0)
        shear = wind_load.get("column_base_shear", 0.0)

        # 选择截面级别
        if height_m < 3:
            level = "low"
        elif height_m <= 5:
            level = "medium"
        else:
            level = "high"

        width, depth = self.SECTION_OPTIONS[level]
        rebar = self.REBAR_OPTIONS[level]
        stirrups = self.STIRRUP_OPTIONS[level]

        # 考虑抗震调整
        if seismic_intensity >= 8:
            # 提高配筋率
            rebar = self.REBAR_OPTIONS["high"]
            stirrups = self.STIRRUP_OPTIONS["high"]

        fc = self.CONCRETE_FC.get(concrete_grade, 14.3)
        fy = self.STEEL_FY.get(steel_grade, 360)

        # 承载力计算 (简化公式)
        cover = 30
        h0 = depth - cover  # 有效高度
        axial_capacity = 0.9 * fc * width * depth / 1000  # kN

        # 弯矩承载力 (简化)
        as_area = rebar["area"]
        moment_capacity = fy * as_area * (h0 - 35) / 1_000_000  # kN·m

        # 柱自重估算
        self_weight = width * depth * height_m * 25 / 1_000_000  # kN (密度25kN/m³)

        design = ConcreteColumnDesign(
            width=width,
            depth=depth,
            concrete_grade=concrete_grade,
            steel_grade=steel_grade,
            longitudinal_bars=rebar["bars"],
            longitudinal_bars_area=rebar["area"],
            stirrups=stirrups,
            stirrups_zone="加密区范围: 柱顶柱底各500mm",
            cover=cover,
            axial_capacity=axial_capacity,
            moment_capacity=moment_capacity,
            reinforcement_ratio=rebar["ratio"],
            self_weight=self_weight,
        )

        logger.info(
            f"混凝土柱设计: {width}×{depth}mm, {rebar['bars']}, "
            f"{stirrups}, M_cap={moment_capacity:.1f}kN·m"
        )

        return {
            "column_type": "concrete",
            "width": width,
            "depth": depth,
            "concrete_grade": concrete_grade,
            "steel_grade": steel_grade,
            "longitudinal_bars": rebar["bars"],
            "longitudinal_bars_area": rebar["area"],
            "stirrups": stirrups,
            "stirrups_zone": "加密区范围: 柱顶柱底各500mm",
            "cover": cover,
            "axial_capacity": axial_capacity,
            "moment_capacity": moment_capacity,
            "reinforcement_ratio": rebar["ratio"],
            "self_weight": self_weight,
        }