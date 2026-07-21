"""LangGraph 工作流编排模块."""

from typing import Any

from langgraph.graph import END, StateGraph

from src.agents.state import AgentState, ProcessingStatus
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


class WallDesignerOrchestrator:
    """围墙设计智能体 - LangGraph 状态图编排器.

    负责串联参数解析 → 模数计算 → 结构设计 → 几何生成 →
    草图生成 → 效果图渲染 → 报告输出的全流程。
    """

    def __init__(self, config: Any | None = None):
        """初始化编排器.

        Args:
            config: 应用配置，None 则使用默认
        """
        self.config = config
        self.graph: StateGraph = StateGraph(AgentState)
        self._build_graph()
        self.agent = self.graph.compile()
        logger.info("WallDesignerOrchestrator 初始化完成")

    def _build_graph(self) -> None:
        """构建 LangGraph 状态图."""
        # 添加节点
        self.graph.add_node("parse_input", self.parse_input)
        self.graph.add_node("calculate_modular", self.calculate_modular)
        self.graph.add_node("structural_design", self.structural_design)
        self.graph.add_node("generate_geometry", self.generate_geometry)
        self.graph.add_node("generate_sketch", self.generate_sketch)
        self.graph.add_node("generate_render", self.generate_render)
        self.graph.add_node("generate_report", self.generate_report)
        self.graph.add_node("handle_error", self.handle_error)

        # 设置入口
        self.graph.set_entry_point("parse_input")

        # 添加边 - 线性流程
        self.graph.add_edge("parse_input", "calculate_modular")
        self.graph.add_edge("calculate_modular", "structural_design")
        self.graph.add_edge("structural_design", "generate_geometry")
        self.graph.add_edge("generate_geometry", "generate_sketch")
        self.graph.add_edge("generate_sketch", "generate_render")
        self.graph.add_edge("generate_render", "generate_report")
        self.graph.add_edge("generate_report", END)

        logger.info("状态图构建完成: 7个处理节点 + 1个错误处理节点")

    # ==================== 处理节点 ====================

    async def parse_input(self, state: AgentState) -> AgentState:
        """参数解析节点 - 将自然语言输入转换为结构化设计参数.

        Args:
            state: 当前状态

        Returns:
            更新后的状态
        """
        logger.info(f"开始参数解析: {state['raw_input'][:80]}...")
        state["status"] = ProcessingStatus.PARSING
        state["progress"] = 0.1

        try:
            parser = ParameterParser(config=self.config)
            parsed = await parser.parse(state["raw_input"])
            state["parsed_params"] = parsed
            state["progress"] = 0.2
            logger.info("参数解析完成")
        except Exception as e:
            logger.error(f"参数解析失败: {e}")
            state["status"] = ProcessingStatus.ERROR
            state["error_message"] = str(e)
            raise

        return state

    async def calculate_modular(self, state: AgentState) -> AgentState:
        """模数计算节点 - 板排布 + 柱位优化.

        Args:
            state: 当前状态

        Returns:
            更新后的状态
        """
        logger.info("开始模数计算...")
        state["status"] = ProcessingStatus.CALCULATING
        state["progress"] = 0.3

        try:
            params = state.get("parsed_params", {})
            if not params:
                raise ValueError("缺少解析后的设计参数")

            calculator = ModularCalculator()
            layout_calculator = PanelLayoutCalculator()

            modular = calculator.calculate(
                wall_length=params.get("wall_length", 0),
                column_spacing=params.get("column_spacing", 0),
                panel_width=params.get("panel_width", 600),
            )

            layout = layout_calculator.calculate(
                modular, params.get("wall_height", 2400), params.get("panel_height", 2400)
            )

            # 合并结果
            result = {**modular, **layout}
            state["modular_result"] = result
            state["progress"] = 0.35
            logger.info("模数计算完成")
        except Exception as e:
            logger.error(f"模数计算失败: {e}")
            state["status"] = ProcessingStatus.ERROR
            state["error_message"] = str(e)
            raise

        return state

    async def structural_design(self, state: AgentState) -> AgentState:
        """结构设计节点 - 风荷载/柱/基础设计.

        Args:
            state: 当前状态

        Returns:
            更新后的状态
        """
        logger.info("开始结构设计...")
        state["status"] = ProcessingStatus.STRUCTURAL_DESIGN
        state["progress"] = 0.4

        try:
            params = state.get("parsed_params", {})
            if not params:
                raise ValueError("缺少设计参数")

            # 1. 风荷载计算
            wind_calculator = WindLoadCalculator()
            wind_load = wind_calculator.calculate(
                height=params.get("wall_height", 2400),
                spacing=params.get("column_spacing", 3000),
                terrain_category=params.get("terrain_category", "C"),
                wind_pressure=params.get("wind_pressure"),
            )
            state["wind_load"] = wind_load

            # 2. 柱设计
            material = params.get("column_material", "concrete")
            if material in ("concrete", "concrete_corten"):
                column_designer = ConcreteColumnDesigner()
            else:
                column_designer = SteelColumnDesigner()

            column_design = column_designer.design(
                height=params.get("wall_height", 2400),
                wind_load=wind_load,
                seismic_intensity=params.get("seismic_intensity", 6),
            )
            state["column_design"] = column_design

            # 3. 基础设计
            foundation_designer = FoundationDesigner()
            foundation_design = foundation_designer.design(
                vertical_load=column_design.get("self_weight", 25),
                moment=wind_load.get("column_base_moment", 0),
                shear=wind_load.get("column_base_shear", 0),
                soil_capacity=self.config.soil_bearing_capacity if self.config else 150.0,
            )
            state["foundation_design"] = foundation_design
            state["progress"] = 0.5
            logger.info("结构设计完成")
        except Exception as e:
            logger.error(f"结构设计失败: {e}")
            state["status"] = ProcessingStatus.ERROR
            state["error_message"] = str(e)
            raise

        return state

    async def generate_geometry(self, state: AgentState) -> AgentState:
        """几何生成节点 - 生成3D模型/线稿/深度图.

        Args:
            state: 当前状态

        Returns:
            更新后的状态
        """
        logger.info("开始几何生成...")
        state["status"] = ProcessingStatus.GEOMETRY
        state["progress"] = 0.55

        try:
            from src.geometry.wall_generator import WallGeometryGenerator

            generator = WallGeometryGenerator(
                modular_result=state.get("modular_result", {}),
                column_design=state.get("column_design", {}),
                foundation_design=state.get("foundation_design", {}),
            )

            output_dir = (
                self.config.output_path / "models" if self.config else None
            )
            if output_dir:
                output_dir.mkdir(parents=True, exist_ok=True)

            # 导出STL
            stl_path = output_dir / "wall_model.stl" if output_dir else None
            if stl_path:
                generator.export_to_stl(str(stl_path))
                state["model_path"] = str(stl_path)

            state["progress"] = 0.6
            logger.info("几何生成完成")
        except Exception as e:
            logger.error(f"几何生成失败: {e}")
            state["status"] = ProcessingStatus.ERROR
            state["error_message"] = str(e)
            raise

        return state

    async def generate_sketch(self, state: AgentState) -> AgentState:
        """草图生成节点 - 生成手绘风格线稿.

        Args:
            state: 当前状态

        Returns:
            更新后的状态
        """
        logger.info("开始草图生成...")
        state["status"] = ProcessingStatus.SKETCH
        state["progress"] = 0.65

        try:
            from src.geometry.export_utils import render_lineart
            from src.sketch.sketch_generator import SketchGenerator

            # 从几何数据生成线稿
            modular = state.get("modular_result", {})
            lineart = render_lineart(
                wall_length=state.get("parsed_params", {}).get("wall_length", 10000),
                wall_height=state.get("parsed_params", {}).get("wall_height", 2400),
                columns=modular.get("columns", []),
                panels=modular.get("total_panels", []),
            )

            # 使用SketchGenerator生成手绘风格
            sketch_gen = SketchGenerator()
            output_dir = (
                self.config.output_path / "sketches" if self.config else None
            )
            if output_dir:
                output_dir.mkdir(parents=True, exist_ok=True)
            sketch_path = output_dir / "elevation_sketch.png" if output_dir else None

            if sketch_path:
                sketch_gen.generate_from_lineart(
                    lineart_image=lineart,
                    output_path=str(sketch_path),
                    with_dimensions=True,
                )
                state["sketch_path"] = str(sketch_path)

            state["progress"] = 0.7
            logger.info("草图生成完成")
        except Exception as e:
            logger.error(f"草图生成失败: {e}")
            state["status"] = ProcessingStatus.ERROR
            state["error_message"] = str(e)
            raise

        return state

    async def generate_render(self, state: AgentState) -> AgentState:
        """效果图生成节点 - 生成逼真彩色渲染.

        Args:
            state: 当前状态

        Returns:
            更新后的状态
        """
        logger.info("开始效果图生成...")
        state["status"] = ProcessingStatus.RENDER
        state["progress"] = 0.75

        try:
            from src.render.render_generator import RenderGenerator

            # 获取材质参数
            params = state.get("parsed_params", {})
            surface_finish = params.get("surface_finish", "fair-faced")
            column_material = params.get("column_material", "concrete")

            render_gen = RenderGenerator()
            output_dir = (
                self.config.output_path / "renders" if self.config else None
            )
            if output_dir:
                output_dir.mkdir(parents=True, exist_ok=True)
            render_path = output_dir / "render_color.png" if output_dir else None

            if render_path:
                render_gen.generate(
                    depth_map=None,  # 待实际集成时传入真实depth_map
                    mask=None,  # 待实际集成时传入真实mask
                    params={
                        "surface_finish": surface_finish,
                        "column_material": column_material,
                    },
                    output_path=str(render_path),
                )
                state["render_path"] = str(render_path)

            state["progress"] = 0.85
            logger.info("效果图生成完成")
        except Exception as e:
            logger.error(f"效果图生成失败: {e}")
            state["status"] = ProcessingStatus.ERROR
            state["error_message"] = str(e)
            raise

        return state

    async def generate_report(self, state: AgentState) -> AgentState:
        """报告生成节点 - 生成计算书和材料清单.

        Args:
            state: 当前状态

        Returns:
            更新后的状态
        """
        logger.info("开始报告生成...")
        state["status"] = ProcessingStatus.REPORT
        state["progress"] = 0.9

        try:
            report_generator = ReportGenerator()
            output_dir = (
                self.config.output_path / "reports" if self.config else None
            )
            if output_dir:
                output_dir.mkdir(parents=True, exist_ok=True)
            report_path = output_dir / "calculation_report.md" if output_dir else None

            if report_path:
                report = report_generator.generate_calculation_report(
                    design_input=state.get("parsed_params", {}),
                    wind_load=state.get("wind_load", {}),
                    column_design=state.get("column_design", {}),
                    foundation_design=state.get("foundation_design", {}),
                )
                with open(report_path, "w", encoding="utf-8") as f:
                    f.write(report)
                state["report_path"] = str(report_path)

            # 生成材料清单
            material_list = report_generator.generate_material_list(
                modular_result=state.get("modular_result", {}),
                column_design=state.get("column_design", {}),
                foundation_design=state.get("foundation_design", {}),
                column_material=state.get("parsed_params", {}).get(
                    "column_material", "concrete"
                ),
            )
            state["material_list"] = material_list

            state["status"] = ProcessingStatus.COMPLETE
            state["progress"] = 1.0
            logger.info("报告生成完成 - 全流程结束")
        except Exception as e:
            logger.error(f"报告生成失败: {e}")
            state["status"] = ProcessingStatus.ERROR
            state["error_message"] = str(e)
            raise

        return state

    async def handle_error(self, state: AgentState) -> AgentState:
        """错误处理节点.

        Args:
            state: 当前状态

        Returns:
            更新后的状态 (status = ERROR)
        """
        logger.error(f"进入错误处理节点: {state.get('error_message')}")
        state["status"] = ProcessingStatus.ERROR
        state["progress"] = -1.0
        return state

    # ==================== 公共接口 ====================

    async def run(self, user_input: str) -> dict[str, Any]:
        """执行完整设计流程.

        Args:
            user_input: 用户自然语言输入

        Returns:
            包含所有阶段结果的字典
        """
        from src.agents.state import create_initial_state

        initial_state = create_initial_state(user_input)
        logger.info("开始执行设计流程...")

        try:
            result = await self.agent.ainvoke(initial_state)
            logger.info(f"设计流程完成: status={result.get('status')}")
            return result  # type: ignore[return-value]
        except Exception as e:
            logger.error(f"设计流程执行失败: {e}")
            return {
                "status": ProcessingStatus.ERROR,
                "error_message": str(e),
                "progress": -1.0,
            }

    def run_sync(self, user_input: str) -> dict[str, Any]:
        """同步执行设计流程 (用于 Gradio 等非异步环境).

        Args:
            user_input: 用户自然语言输入

        Returns:
            包含所有阶段结果的字典
        """
        import asyncio

        return asyncio.run(self.run(user_input))