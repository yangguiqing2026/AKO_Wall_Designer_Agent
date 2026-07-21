"""风荷载计算模块 - 依据 GB 50009-2012."""

from typing import Any

from src.utils.logging import get_logger

logger = get_logger(__name__)


class WindLoadCalculator:
    """风荷载计算器 - 计算作用于围墙的风荷载.

    依据 GB 50009-2012《建筑结构荷载规范》
    wk = βz * μs * μz * w0
    """

    # 风压高度变化系数 μz (地面粗糙度 A/B/C/D)
    HEIGHT_COEFFICIENTS: dict[str, dict[int, float]] = {
        "A": {5: 1.09, 10: 1.28, 15: 1.42, 20: 1.52, 30: 1.67, 40: 1.79, 50: 1.89},
        "B": {5: 1.00, 10: 1.00, 15: 1.13, 20: 1.23, 30: 1.39, 40: 1.52, 50: 1.62},
        "C": {5: 0.65, 10: 0.65, 15: 0.65, 20: 0.74, 30: 0.88, 40: 1.00, 50: 1.10},
        "D": {5: 0.51, 10: 0.51, 15: 0.51, 20: 0.51, 30: 0.51, 40: 0.60, 50: 0.69},
    }

    # 全国主要城市基本风压 (kN/m²) R=50年
    DEFAULT_WIND_PRESSURES: dict[str, float] = {
        "北京": 0.45,
        "上海": 0.55,
        "广州": 0.50,
        "深圳": 0.75,
        "成都": 0.30,
        "武汉": 0.35,
        "西安": 0.35,
        "乌鲁木齐": 0.60,
        "哈尔滨": 0.55,
        "沈阳": 0.55,
        "天津": 0.50,
        "重庆": 0.40,
        "南京": 0.40,
        "杭州": 0.45,
        "福州": 0.70,
        "厦门": 0.80,
        "海口": 0.75,
    }

    def __init__(self):
        """初始化风荷载计算器."""
        pass

    def calculate(
        self,
        height: float,
        spacing: float,
        terrain_category: str = "C",
        wind_pressure: float | None = None,
        city: str = "",
    ) -> dict[str, float]:
        """计算作用于扶壁柱的风荷载.

        Args:
            height: 围墙高度 (mm)
            spacing: 柱间距 (mm)
            terrain_category: 地面粗糙度类别 A/B/C/D
            wind_pressure: 基本风压 (kN/m²), None则自动查表
            city: 城市名称 (用于自动查风压)

        Returns:
            风荷载计算结果字典
        """
        # 基本风压 w0
        w0 = wind_pressure if wind_pressure else self._get_wind_pressure(city)
        if w0 is None:
            w0 = 0.45  # 默认值
            logger.warning(f"未指定风压，使用默认值 {w0} kN/m²")

        # 风压高度变化系数 μz
        mu_z = self._get_height_coefficient(height, terrain_category)

        # 风振系数 βz (围墙取1.0)
        beta_z = 1.0

        # 体型系数 μs (围墙取1.3)
        mu_s = 1.3

        # 标准风压 wk = βz * μs * μz * w0
        wk = beta_z * mu_s * mu_z * w0

        # 高度转换为 m
        height_m = height / 1000.0
        spacing_m = spacing / 1000.0

        # 单柱受荷宽度 = 柱间距
        tributary_width = spacing_m

        # 柱底水平力 (kN)
        total_force = wk * tributary_width * height_m

        # 柱底弯矩 (kN·m) - 均布荷载导致的悬臂弯矩
        moment = total_force * height_m / 2.0

        # 柱底剪力 = 总水平力
        shear = total_force

        result = {
            "basic_wind_pressure": w0,
            "height_coefficient": mu_z,
            "gust_factor": beta_z,
            "shape_coefficient": mu_s,
            "standard_wind_pressure": wk,
            "total_horizontal_force": total_force,
            "column_base_moment": moment,
            "column_base_shear": shear,
        }

        logger.info(
            f"风荷载计算: w0={w0}, μz={mu_z}, wk={wk:.3f}, "
            f"F={total_force:.2f}kN, M={moment:.2f}kN·m"
        )
        return result

    def _get_height_coefficient(self, height: float, terrain: str) -> float:
        """获取风压高度变化系数 μz.

        Args:
            height: 高度 (mm)
            terrain: 地面粗糙度

        Returns:
            高度变化系数
        """
        height_m = height / 1000.0
        coeffs = self.HEIGHT_COEFFICIENTS.get(terrain, self.HEIGHT_COEFFICIENTS["C"])

        # 找到最近的参考高度
        ref_heights = sorted(coeffs.keys())
        for ref in ref_heights:
            if height_m <= ref:
                return coeffs[ref]

        return coeffs[ref_heights[-1]]

    def _get_wind_pressure(self, city: str) -> float | None:
        """根据城市名称查找基本风压.

        Args:
            city: 城市名称

        Returns:
            基本风压值, 找不到返回 None
        """
        if not city:
            return None
        for key, value in self.DEFAULT_WIND_PRESSURES.items():
            if city in key or key in city:
                return value
        return None