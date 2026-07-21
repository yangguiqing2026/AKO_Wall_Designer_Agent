"""Tests for modular calculator modules."""

from src.calculators.modular_calculator import ModularCalculator
from src.calculators.panel_layout import PanelLayoutCalculator


class TestModularCalculator:
    """模数计算器测试."""

    def test_standard_wall(self):
        """测试标准围墙模数计算."""
        calc = ModularCalculator()
        result = calc.calculate(
            wall_length=30000,
            column_spacing=3600,
            panel_width=600,
            column_width=300,
        )
        assert result["num_spans"] > 0
        assert result["panels_per_span"] > 0
        assert len(result["total_panels"]) > 0
        assert len(result["columns"]) == result["num_spans"] + 1

    def test_perfect_modular_match(self):
        """测试完美模数匹配 (无余量)."""
        calc = ModularCalculator()
        # 3600 间距: 净距 = 3600-300 = 3300, 3300/600 = 5.5 板
        result = calc.calculate(
            wall_length=9600,  # 2跨
            column_spacing=3600,
            panel_width=600,
            column_width=300,
        )
        assert result["num_spans"] > 0
        assert len(result["columns"]) == result["num_spans"] + 1

    def test_short_wall(self):
        """测试短围墙."""
        calc = ModularCalculator()
        result = calc.calculate(
            wall_length=3000,
            column_spacing=3000,
            panel_width=600,
            column_width=300,
        )
        assert result["num_spans"] >= 1
        assert len(result["columns"]) >= 2

    def test_output_structure(self):
        """测试输出结构完整性."""
        calc = ModularCalculator()
        result = calc.calculate(
            wall_length=50000,
            column_spacing=3600,
            panel_width=600,
            column_width=300,
            column_material="concrete",
        )
        required_keys = [
            "panels_per_span",
            "actual_spacing",
            "num_spans",
            "total_panels",
            "columns",
            "remainder",
            "adjustment_message",
        ]
        for key in required_keys:
            assert key in result, f"缺少键: {key}"

    def test_non_standard_panel(self):
        """测试非标面板生成."""
        calc = ModularCalculator()
        result = calc.calculate(
            wall_length=10000,  # 非整模数
            column_spacing=3600,
            panel_width=600,
            column_width=300,
        )
        non_standard = sum(
            1 for p in result["total_panels"] if not p["is_standard"]
        )
        assert result["non_standard_panel_count"] == non_standard


class TestPanelLayoutCalculator:
    """面板布局计算器测试."""

    def test_single_layer(self):
        """测试单层布局."""
        calc = PanelLayoutCalculator()
        modular = {
            "total_panels": [{"width": 600, "height": 2400}],
            "columns": [{"height": 2400}],
        }
        result = calc.calculate(modular, wall_height=2400, panel_height=2400)
        assert result["total_height_layers"] == 1
        assert result["actual_wall_height"] == 2400
        assert not result["is_height_adjusted"]

    def test_multi_layer(self):
        """测试多层布局."""
        calc = PanelLayoutCalculator()
        modular = {
            "total_panels": [
                {"width": 600, "height": 1200, "is_standard": True,
                 "position_x": 300, "position_y": 0, "layer_index": 0}
            ],
            "columns": [{"width": 300, "depth": 400, "height": 4800,
                         "position_x": 150, "material": "concrete", "index": 0}],
        }
        result = calc.calculate(modular, wall_height=4800, panel_height=1200)
        assert result["total_height_layers"] == 4
        assert result["actual_wall_height"] == 4800