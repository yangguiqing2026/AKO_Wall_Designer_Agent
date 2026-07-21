"""钢柱设计模块 - 依据 GB 50017-2017."""

from dataclasses import dataclass
from typing import Any

from src.structural.section_library import HSteelSection, SectionLibrary
from src.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class SteelColumnDesign:
    """钢柱设计结果."""

    section_type: str
    section_label: str
    area: float
    ix: float
    iy: float
    wx: float
    steel_grade: str
    base_plate: str
    anchor_bolts: str
    stiffener: str
    axial_capacity: float
    moment_capacity: float
    self_weight: float


class SteelColumnDesigner:
    """钢扶壁柱设计器 - 选用H型钢截面.

    依据 GB 50017-2017《钢结构设计标准》。
    """

    def __init__(self):
        """初始化钢柱设计器."""
        self.section_lib = SectionLibrary()

    def design(
        self,
        height: float,
        wind_load: dict[str, float],
        seismic_intensity: int = 6,
        steel_grade: str = "Q355B",
    ) -> dict[str, Any]:
        """设计钢柱截面.

        Args:
            height: 围墙高度 (mm)
            wind_load: 风荷载计算结果
            seismic_intensity: 抗震设防烈度
            steel_grade: 钢材牌号

        Returns:
            钢柱设计结果字典
        """
        height_m = height / 1000.0
        moment = wind_load.get("column_base_moment", 0.0)  # kN·m
        shear = wind_load.get("column_base_shear", 0.0)  # kN

        # 选择截面: 根据弯矩需求
        section = self._select_section(height_m, moment, steel_grade)

        # 柱脚底板设计
        base_plate, anchor_bolts, stiffener = self._design_base_plate(
            section, moment, shear
        )

        # 承载力
        fy = 355 if "355" in steel_grade else 345 if "345" in steel_grade else 235
        axial_capacity = section.area * fy / 10  # kN (简化)
        moment_capacity = section.wx * fy / 1000  # kN·m (简化公式 M = Wx * fy)

        # 自重
        self_weight = section.area * height_m * 78.5 / 1000  # kN (密度78.5kN/m³)

        design = SteelColumnDesign(
            section_type="H型钢",
            section_label=section.label,
            area=section.area,
            ix=section.ix,
            iy=section.iy,
            wx=section.wx,
            steel_grade=steel_grade,
            base_plate=base_plate,
            anchor_bolts=anchor_bolts,
            stiffener=stiffener,
            axial_capacity=axial_capacity,
            moment_capacity=moment_capacity,
            self_weight=self_weight,
        )

        logger.info(
            f"钢柱设计: {section.label}, area={section.area}cm², "
            f"M_cap={moment_capacity:.1f}kN·m"
        )

        return {
            "column_type": "steel",
            "section_type": "H型钢",
            "section_label": section.label,
            "area": section.area,
            "ix": section.ix,
            "iy": section.iy,
            "wx": section.wx,
            "steel_grade": steel_grade,
            "base_plate": base_plate,
            "anchor_bolts": anchor_bolts,
            "stiffener": stiffener,
            "axial_capacity": axial_capacity,
            "moment_capacity": moment_capacity,
            "self_weight": self_weight,
        }

    def _select_section(
        self, height_m: float, moment: float, steel_grade: str
    ) -> HSteelSection:
        """根据高度和弯矩选择H型钢截面.

        Args:
            height_m: 高度 (m)
            moment: 柱底弯矩 (kN·m)
            steel_grade: 钢材牌号

        Returns:
            选定的H型钢截面
        """
        # 估算需要的截面模量 W_req = M / fy
        fy = 355 if "355" in steel_grade else 345
        w_required = moment * 1000 / fy  # cm³

        candidates = self.section_lib.get_h_sections()
        selected = candidates[0]

        for section in candidates:
            if section.wx >= w_required:
                selected = section
                break
        else:
            # 都不满足，选最大的
            selected = candidates[-1]

        return selected

    def _design_base_plate(
        self, section: HSteelSection, moment: float, shear: float
    ) -> tuple[str, str, str]:
        """设计柱脚底板和锚栓.

        Args:
            section: 选定的H型钢截面
            moment: 柱底弯矩 (kN·m)
            shear: 柱底剪力 (kN)

        Returns:
            (底板规格, 锚栓规格, 加劲肋规格)
        """
        # 按弯矩和截面大小确定底板尺寸
        if moment < 10:
            plate = "-16×300×300"
            bolts = "4-M20"
            stiff = "无需加劲肋"
        elif moment < 30:
            plate = "-20×400×400"
            bolts = "4-M24"
            stiff = "-10×80加劲肋×4"
        elif moment < 60:
            plate = "-25×500×500"
            bolts = "4-M30"
            stiff = "-12×100加劲肋×4"
        else:
            plate = "-30×600×600"
            bolts = "8-M30"
            stiff = "-16×120加劲肋×6"

        return plate, bolts, stiff