"""Tests for parameter parser module."""

import pytest

from src.parsers.parameter_parser import (
    ColumnMaterial,
    DesignInput,
    ParameterParser,
    TerrainCategory,
)


class TestDesignInput:
    """DesignInput Pydantic 模型测试."""

    def test_valid_input(self):
        """测试有效的设计输入."""
        data = {
            "wall_length": 50000,
            "wall_height": 2400,
            "column_spacing": 3600,
            "column_material": "concrete",
            "surface_finish": "fair-faced",
        }
        result = DesignInput(**data)
        assert result.wall_length == 50000
        assert result.panel_width == 600  # 默认值
        assert result.column_width == 300.0  # 混凝土默认柱宽

    def test_steel_default_column_width(self):
        """测试钢柱默认柱宽."""
        data = {
            "wall_length": 30000,
            "wall_height": 2400,
            "column_spacing": 3600,
            "column_material": "steel",
            "surface_finish": "fair-faced",
        }
        result = DesignInput(**data)
        assert result.column_width == 250.0

    def test_zero_values_get_defaults(self):
        """测试 0 值被自动修正为默认值."""
        data = {
            "wall_length": 0,
            "wall_height": 0,
            "column_spacing": 0,
            "column_material": "concrete",
        }
        result = DesignInput(**data)
        assert result.wall_length == 50000.0
        assert result.wall_height == 2400.0
        assert result.column_spacing == 3600.0
        assert result.column_width == 300.0  # 混凝土默认柱宽

    def test_seismic_intensity_range(self):
        """测试抗震烈度范围."""
        data = {
            "wall_length": 10000,
            "wall_height": 2400,
            "column_spacing": 3600,
            "column_material": "concrete",
            "seismic_intensity": 10,  # 超出范围
        }
        with pytest.raises(ValueError):
            DesignInput(**data)


class TestParameterParser:
    """ParameterParser 规则解析测试."""

    def test_parse_concrete_wall(self):
        """测试混凝土围墙解析."""
        parser = ParameterParser(use_llm=False)
        result = parser._parse_with_rules(
            "设计一段50米长的清水混凝土围墙，高度2.4米，柱间距3.6米"
        )
        assert result["wall_length"] == 50000
        assert result["wall_height"] == 2400
        assert result["column_spacing"] == 3600
        assert result["column_material"] == "concrete"

    def test_parse_steel_wall(self):
        """测试钢柱围墙解析."""
        parser = ParameterParser(use_llm=False)
        result = parser._parse_with_rules(
            "100米钢柱围墙，高3米，柱距4.2米，深圳地区"
        )
        assert result["wall_length"] == 100000
        assert result["wall_height"] == 3000
        assert result["column_material"] == "steel"

    def test_parse_with_seismic(self):
        """测试带抗震烈度的解析."""
        parser = ParameterParser(use_llm=False)
        result = parser._parse_with_rules(
            "30米围墙，高2.4米，柱距3米，8度抗震"
        )
        assert result["seismic_intensity"] == 8
        assert result["wall_length"] == 30000