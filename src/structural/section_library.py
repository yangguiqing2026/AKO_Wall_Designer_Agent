# ============================================
# Author: AKO_studio
# Agent: AKO_wall_designer_agent
# Generated: 2026-07-30
# ============================================
#
"""型钢截面库模块."""

from dataclasses import dataclass
from typing import List

from src.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class HSteelSection:
    """H型钢截面属性."""

    label: str  # 型号名称
    height: int  # 总高 H (mm)
    width: int  # 宽度 B (mm)
    t1: float  # 腹板厚度 tw (mm)
    t2: float  # 翼缘厚度 tf (mm)
    area: float  # 截面面积 (cm²)
    ix: float  # 惯性矩 Ix (cm⁴)
    iy: float  # 惯性矩 Iy (cm⁴)
    wx: float  # 截面模量 Wx (cm³)
    wy: float  # 截面模量 Wy (cm³)
    weight: float  # 每米理论重量 (kg/m)


class SectionLibrary:
    """标准型钢截面库.

    包含常用H型钢 (HW宽翼缘) 和方矩管截面。
    """

    # HW系列宽翼缘H型钢 (GB/T 11263-2017)
    H_SECTIONS: dict[str, HSteelSection] = {
        "HW150×150": HSteelSection(
            label="HW150×150×7×10",
            height=150, width=150, t1=7.0, t2=10.0,
            area=40.55, ix=1660, iy=564, wx=221, wy=75.1, weight=31.9,
        ),
        "HW175×175": HSteelSection(
            label="HW175×175×7.5×11",
            height=175, width=175, t1=7.5, t2=11.0,
            area=51.43, ix=2880, iy=984, wx=327, wy=112, weight=40.4,
        ),
        "HW200×200": HSteelSection(
            label="HW200×200×8×12",
            height=200, width=200, t1=8.0, t2=12.0,
            area=63.53, ix=4720, iy=1600, wx=472, wy=160, weight=49.9,
        ),
        "HW250×250": HSteelSection(
            label="HW250×250×9×14",
            height=250, width=250, t1=9.0, t2=14.0,
            area=92.18, ix=10800, iy=3650, wx=862, wy=292, weight=72.4,
        ),
        "HW300×300": HSteelSection(
            label="HW300×300×10×15",
            height=300, width=300, t1=10.0, t2=15.0,
            area=120.4, ix=20500, iy=6760, wx=1360, wy=451, weight=94.5,
        ),
        "HW350×350": HSteelSection(
            label="HW350×350×12×19",
            height=350, width=350, t1=12.0, t2=19.0,
            area=173.9, ix=40300, iy=13600, wx=2300, wy=776, weight=137,
        ),
    }

    def get_h_sections(self) -> List[HSteelSection]:
        """获取所有H型钢截面 (按wx升序排列).

        Returns:
            按截面模量排序的H型钢列表
        """
        sections = list(self.H_SECTIONS.values())
        sections.sort(key=lambda s: s.wx)
        return sections

    def get_by_label(self, label: str) -> HSteelSection | None:
        """根据型号获取截面.

        Args:
            label: 型号名称，如 "HW200×200"

        Returns:
            HSteelSection 或 None
        """
        return self.H_SECTIONS.get(label)

    def find_nearest_by_wx(self, wx_required: float) -> HSteelSection:
        """根据需要的截面模量查找最近截面.

        Args:
            wx_required: 需要的截面模量 (cm³)

        Returns:
            最接近的H型钢截面
        """
        sections = self.get_h_sections()
        for section in sections:
            if section.wx >= wx_required:
                return section
        return sections[-1]