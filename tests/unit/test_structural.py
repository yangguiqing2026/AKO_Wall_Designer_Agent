"""Tests for structural design modules."""

from src.structural.concrete_column import ConcreteColumnDesigner
from src.structural.foundation import FoundationDesigner
from src.structural.section_library import SectionLibrary
from src.structural.steel_column import SteelColumnDesigner
from src.structural.wind_load import WindLoadCalculator


class TestWindLoad:
    """风荷载计算测试."""

    def test_default_wind_load(self):
        """测试默认风荷载计算."""
        calc = WindLoadCalculator()
        result = calc.calculate(
            height=2400,
            spacing=3600,
            terrain_category="C",
            wind_pressure=0.45,
        )
        assert "standard_wind_pressure" in result
        assert "column_base_moment" in result
        assert result["basic_wind_pressure"] == 0.45
        assert result["total_horizontal_force"] > 0

    def test_full_parameters(self):
        """测试完整参数风荷载计算."""
        calc = WindLoadCalculator()
        result = calc.calculate(
            height=3000,
            spacing=4200,
            terrain_category="B",
            wind_pressure=0.75,
            city="深圳",
        )
        assert result["basic_wind_pressure"] == 0.75
        assert result["shape_coefficient"] == 1.3
        assert result["gust_factor"] == 1.0


class TestConcreteColumn:
    """混凝土柱设计测试."""

    def test_low_wall_column(self):
        """测试矮墙柱设计."""
        designer = ConcreteColumnDesigner()
        wind_load = {
            "column_base_moment": 2.0,
            "column_base_shear": 1.5,
        }
        result = designer.design(height=2400, wind_load=wind_load)
        assert result["width"] == 300
        assert result["concrete_grade"] == "C30"
        assert "4Φ" in result["longitudinal_bars"]

    def test_high_wall_column(self):
        """测试高墙柱设计."""
        designer = ConcreteColumnDesigner()
        wind_load = {
            "column_base_moment": 45.0,
            "column_base_shear": 15.0,
        }
        result = designer.design(height=6000, wind_load=wind_load)
        assert result["width"] == 350
        assert result["depth"] == 450
        assert "6Φ" in result["longitudinal_bars"]

    def test_seismic_high(self):
        """测试高抗震烈度柱设计."""
        designer = ConcreteColumnDesigner()
        wind_load = {
            "column_base_moment": 20.0,
            "column_base_shear": 8.0,
        }
        result = designer.design(
            height=3600, wind_load=wind_load, seismic_intensity=8
        )
        assert result["reinforcement_ratio"] >= 0.85


class TestSteelColumn:
    """钢柱设计测试."""

    def test_steel_section_selection(self):
        """测试钢柱截面选择."""
        designer = SteelColumnDesigner()
        wind_load = {
            "column_base_moment": 15.0,
            "column_base_shear": 5.0,
        }
        result = designer.design(height=2400, wind_load=wind_load)
        assert result["column_type"] == "steel"
        assert "HW" in result["section_label"]
        assert result["section_label"] in ["HW150×150×7×10", "HW175×175×7.5×11", "HW200×200×8×12"]


class TestFoundation:
    """基础设计测试."""

    def test_foundation_design(self):
        """测试基础设计."""
        designer = FoundationDesigner()
        result = designer.design(
            vertical_load=25.0,
            moment=10.0,
            shear=5.0,
            soil_capacity=150.0,
        )
        assert result["foundation_type"] == "独立基础"
        assert result["base_length"] >= 600
        assert result["height"] >= 400
        assert result["overturning_ratio"] > 0
        assert result["sliding_ratio"] > 0


class TestSectionLibrary:
    """型钢截面库测试."""

    def test_get_sections(self):
        """测试获取所有截面."""
        lib = SectionLibrary()
        sections = lib.get_h_sections()
        assert len(sections) == 6
        assert sections[0].label.startswith("HW")

    def test_find_by_wx(self):
        """测试按截面模量查找."""
        lib = SectionLibrary()
        section = lib.find_nearest_by_wx(500)
        assert section.wx >= 500 or section == lib.get_h_sections()[-1]

    def test_get_by_label(self):
        """测试按型号查找."""
        lib = SectionLibrary()
        section = lib.get_by_label("HW200×200")
        assert section is not None
        assert section.area == 63.53