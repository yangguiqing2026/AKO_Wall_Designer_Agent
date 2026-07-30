# ============================================
# Author: AKO_studio
# Agent: AKO_wall_designer_agent
# Generated: 2026-07-30
# ============================================
#
"""分步编排器 - 支持逐层交互式设计."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from src.calculators.modular_calculator import ModularCalculator
from src.calculators.panel_layout import PanelLayoutCalculator
from src.parsers.parameter_parser import ParameterParser
from src.reports.report_generator import ReportGenerator
from src.structural.concrete_column import ConcreteColumnDesigner
from src.structural.foundation import FoundationDesigner
from src.structural.steel_column import SteelColumnDesigner
from src.structural.wind_load import WindLoadCalculator
from src.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class DesignState:
    """设计中间状态 - 在各步骤间传递."""

    raw_input: str = ""
    parsed_params: dict[str, Any] = field(default_factory=dict)
    modular_result: dict[str, Any] = field(default_factory=dict)
    wind_load: dict[str, float] = field(default_factory=dict)
    column_design: dict[str, Any] = field(default_factory=dict)
    foundation_design: dict[str, Any] = field(default_factory=dict)
    report_path: Optional[str] = None
    sketch_path: Optional[str] = None
    render_path: Optional[str] = None
    stl_path: Optional[str] = None
    material_list: Optional[dict[str, Any]] = None
    current_step: int = 0


class StepOrchestrator:
    """分步设计编排器 - 将7阶段流水线拆分为5个交互步骤.

    Step 1: 参数解析 + 模数计算
    Step 2: 结构设计 (风荷载/柱/基础) + 计算书
    Step 3: 草图生成
    Step 4: 效果图生成
    Step 5: 3D模型导出
    """

    def __init__(self, config: Any | None = None):
        self.config = config
        self.output_path = config.output_path if config else Path("./outputs")
        self.output_path.mkdir(parents=True, exist_ok=True)
        (self.output_path / "sketches").mkdir(exist_ok=True)
        (self.output_path / "renders").mkdir(exist_ok=True)
        (self.output_path / "reports").mkdir(exist_ok=True)
        (self.output_path / "models").mkdir(exist_ok=True)
        logger.info("StepOrchestrator 初始化完成")

    # ==================== Step 1: 参数解析 + 模数计算 ====================

    def step1_parse_and_modular(
        self,
        raw_input: str,
        quick_params: dict[str, Any] | None = None,
    ) -> DesignState:
        """执行第一步: 参数解析 + 模数计算.

        Args:
            raw_input: 用户自然语言输入
            quick_params: UI 面板快速参数 (优先于 LLM 解析)

        Returns:
            DesignState 含 parsed_params + modular_result
        """
        state = DesignState(raw_input=raw_input)
        logger.info("Step 1: 参数解析 + 模数计算")

        # 1a. 参数解析
        if quick_params and any(quick_params.values()):
            # 使用 UI 面板参数
            params = {
                "wall_length": float(quick_params.get("wall_length", 50000)),
                "wall_height": float(quick_params.get("wall_height", 2400)),
                "column_spacing": float(quick_params.get("column_spacing", 3600)),
                "column_material": quick_params.get("column_material", "concrete"),
                "panel_width": float(quick_params.get("panel_width", 600)),
                "panel_height": 2400.0,
                "column_width": None,
                "wind_pressure": quick_params.get("wind_pressure"),
                "terrain_category": quick_params.get("terrain_category", "C"),
                "surface_finish": quick_params.get("surface_finish", "fair-faced"),
                "seismic_intensity": int(quick_params.get("seismic_intensity", 6)),
            }
            logger.info("使用 UI 面板快速参数")
        else:
            # LLM 解析
            parser = ParameterParser(config=self.config)
            import asyncio
            params = asyncio.run(parser.parse(raw_input))

        # Pydantic 校验 (处理 column_width 默认值)
        from src.parsers.parameter_parser import DesignInput
        validated = DesignInput(**params)
        state.parsed_params = validated.model_dump()

        # 1b. 模数计算
        calculator = ModularCalculator()
        layout_calc = PanelLayoutCalculator()

        modular = calculator.calculate(
            wall_length=state.parsed_params.get("wall_length", 0),
            column_spacing=state.parsed_params.get("column_spacing", 0),
            panel_width=state.parsed_params.get("panel_width", 600),
            column_width=state.parsed_params.get("column_width", 300),
            column_material=state.parsed_params.get("column_material", "concrete"),
        )

        layout = layout_calc.calculate(
            modular,
            state.parsed_params.get("wall_height", 2400),
            state.parsed_params.get("panel_height", 2400),
        )

        state.modular_result = {**modular, **layout}
        state.current_step = 1

        total_panels = len(state.modular_result.get("total_panels", []))
        num_columns = len(state.modular_result.get("columns", []))
        num_spans = state.modular_result.get("num_spans", 0)
        adj_msg = state.modular_result.get("adjustment_message", "")

        logger.info(
            f"Step 1 完成: {num_spans}跨, {total_panels}板, {num_columns}柱"
        )
        if adj_msg:
            logger.info(f"  调整: {adj_msg}")

        return state

    # ==================== Step 2: 结构设计 + 计算书 ====================

    def step2_structural_design(self, state: DesignState) -> DesignState:
        """执行第二步: 风荷载/柱/基础设计 + 生成计算书.

        Args:
            state: 当前设计状态

        Returns:
            更新后的 DesignState
        """
        logger.info("Step 2: 结构设计")
        params = state.parsed_params

        # 2a. 风荷载
        wind_calc = WindLoadCalculator()
        state.wind_load = wind_calc.calculate(
            height=params.get("wall_height", 2400),
            spacing=params.get("column_spacing", 3000),
            terrain_category=params.get("terrain_category", "C"),
            wind_pressure=params.get("wind_pressure"),
        )

        # 2b. 柱设计
        material = params.get("column_material", "concrete")
        if material in ("concrete", "concrete_corten"):
            col_designer = ConcreteColumnDesigner()
        else:
            col_designer = SteelColumnDesigner()

        state.column_design = col_designer.design(
            height=params.get("wall_height", 2400),
            wind_load=state.wind_load,
            seismic_intensity=params.get("seismic_intensity", 6),
        )

        # 2c. 基础设计
        foundation_designer = FoundationDesigner()
        soil_capacity = (
            self.config.soil_bearing_capacity if self.config else 150.0
        )
        state.foundation_design = foundation_designer.design(
            vertical_load=state.column_design.get("self_weight", 25),
            moment=state.wind_load.get("column_base_moment", 0),
            shear=state.wind_load.get("column_base_shear", 0),
            soil_capacity=soil_capacity,
        )

        # 2d. 生成计算书
        report_gen = ReportGenerator()
        report = report_gen.generate_calculation_report(
            design_input=params,
            wind_load=state.wind_load,
            column_design=state.column_design,
            foundation_design=state.foundation_design,
        )
        report_path = self.output_path / "reports" / "calculation_report.md"
        report_path.write_text(report, encoding="utf-8")
        state.report_path = str(report_path)

        # 材料清单
        state.material_list = report_gen.generate_material_list(
            modular_result=state.modular_result,
            column_design=state.column_design,
            foundation_design=state.foundation_design,
            column_material=material,
        )

        state.current_step = 2
        logger.info(f"Step 2 完成: 报告 → {report_path}")
        return state

    # ==================== Step 3: 草图生成 ====================

    def step3_sketch(self, state: DesignState) -> DesignState:
        """执行第三步: 生成立面草图.

        Args:
            state: 当前设计状态

        Returns:
            更新后的 DesignState
        """
        logger.info("Step 3: 草图生成")
        params = state.parsed_params
        modular = state.modular_result

        from src.geometry.export_utils import render_lineart
        from src.sketch.sketch_generator import SketchGenerator

        # 生成线稿
        lineart = render_lineart(
            wall_length=params.get("wall_length", 10000),
            wall_height=params.get("wall_height", 2400),
            columns=modular.get("columns", []),
            panels=modular.get("total_panels", []),
        )

        # 生成手绘风格草图
        sketch_gen = SketchGenerator()
        sketch_path = str(self.output_path / "sketches" / "elevation_sketch.png")
        sketch_gen.generate_from_lineart(
            lineart_image=lineart,
            output_path=sketch_path,
            with_dimensions=True,
        )

        state.sketch_path = sketch_path
        state.current_step = 3
        logger.info(f"Step 3 完成: 草图 → {sketch_path}")
        return state

    # ==================== Step 4: 效果图生成 ====================

    def step4_render(self, state: DesignState) -> DesignState:
        """执行第四步: 生成彩色效果图.

        Args:
            state: 当前设计状态

        Returns:
            更新后的 DesignState
        """
        logger.info("Step 4: 效果图生成")
        params = state.parsed_params

        from src.render.render_generator import RenderGenerator

        render_gen = RenderGenerator()
        render_path = str(self.output_path / "renders" / "render_color.png")

        render_gen.generate(
            depth_map=None,
            mask=None,
            params={
                "surface_finish": params.get("surface_finish", "fair-faced"),
                "column_material": params.get("column_material", "concrete"),
            },
            output_path=render_path,
        )

        state.render_path = render_path
        state.current_step = 4
        logger.info(f"Step 4 完成: 效果图 → {render_path}")
        return state

    # ==================== Step 5: 3D 模型导出 ====================

    def step5_3d_model(self, state: DesignState) -> DesignState:
        """执行第五步: 导出 3D STL 模型.

        Args:
            state: 当前设计状态

        Returns:
            更新后的 DesignState
        """
        logger.info("Step 5: 3D 模型导出")

        from src.geometry.wall_generator import WallGeometryGenerator

        generator = WallGeometryGenerator(
            modular_result=state.modular_result,
            column_design=state.column_design,
            foundation_design=state.foundation_design,
        )

        stl_path = str(self.output_path / "models" / "wall_model.stl")
        success = generator.export_to_stl(stl_path)

        if success:
            state.stl_path = stl_path
            logger.info(f"Step 5 完成: STL → {stl_path}")
        else:
            logger.warning("Step 5: STL 导出失败 (可能缺少 CadQuery)")
            state.stl_path = None

        state.current_step = 5
        return state

    # ==================== 完整流程 ====================

    def run_all(self, raw_input: str, quick_params: dict[str, Any] | None = None) -> DesignState:
        """执行全部 5 个步骤.

        Args:
            raw_input: 用户输入
            quick_params: 快速参数

        Returns:
            完整的 DesignState
        """
        state = self.step1_parse_and_modular(raw_input, quick_params)
        state = self.step2_structural_design(state)
        state = self.step3_sketch(state)
        state = self.step4_render(state)
        state = self.step5_3d_model(state)
        return state