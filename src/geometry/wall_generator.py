# ============================================
# Author: AKO_studio
# Agent: AKO_wall_designer_agent
# Generated: 2026-07-30
# ============================================
#
"""围墙几何生成模块 - 使用 CadQuery 生成精确3D模型."""

from typing import Any

from src.utils.logging import get_logger

logger = get_logger(__name__)


class WallGeometryGenerator:
    """围墙3D几何生成器 - 基于 CadQuery 的精确建模.

    生成墙板、扶壁柱、基础的3D组合模型。
    """

    # 默认尺寸参数
    PANEL_THICKNESS: float = 200.0  # 墙板厚度 (mm)
    DEFAULT_COLUMN_DEPTH: float = 400.0  # 柱深度 (mm)

    def __init__(
        self,
        modular_result: dict[str, Any],
        column_design: dict[str, Any],
        foundation_design: dict[str, Any],
    ):
        """初始化几何生成器.

        Args:
            modular_result: 模数计算结果
            column_design: 柱设计结果
            foundation_design: 基础设计结果
        """
        self.modular = modular_result
        self.column = column_design
        self.foundation = foundation_design
        self.panel_thickness = self.PANEL_THICKNESS
        self.column_depth = column_design.get("depth", self.DEFAULT_COLUMN_DEPTH)

        logger.info("WallGeometryGenerator 初始化完成")

    def generate_3d_model(self):
        """生成完整的围墙3D模型 (CadQuery Workplane).

        Returns:
            CadQuery Workplane 对象 (或 None 如果 CadQuery 不可用)
        """
        try:
            import cadquery as cq  # type: ignore[import-untyped]

            model = cq.Workplane("XY")

            # 添加墙板
            panels = self.modular.get("total_panels", [])
            for panel in panels:
                panel_obj = self._create_panel_cq(cq, panel)
                model = model.add(panel_obj)

            # 添加柱
            columns = self.modular.get("columns", [])
            for col in columns:
                col_obj = self._create_column_cq(cq, col)
                model = model.add(col_obj)

            # 添加基础
            for col in columns:
                footing_obj = self._create_footing_cq(cq, col)
                model = model.add(footing_obj)

            logger.info(
                f"3D模型生成完成: {len(panels)} 板, {len(columns)} 柱"
            )
            return model

        except ImportError:
            logger.warning("CadQuery 未安装，无法生成3D模型")
            return None

    def _create_panel_cq(self, cq, panel: dict[str, Any]) -> Any:
        """创建单个墙板 CadQuery 几何体.

        Args:
            cq: CadQuery 模块
            panel: 面板数据

        Returns:
            CadQuery Workplane
        """
        w = panel.get("width", 600)
        h = panel.get("height", 2400)
        px = panel.get("position_x", 0)
        py = panel.get("position_y", 0)

        return (
            cq.Workplane("XY")
            .box(w, h, self.panel_thickness)
            .translate((px, py, self.panel_thickness / 2))
        )

    def _create_column_cq(self, cq, col: dict[str, Any]) -> Any:
        """创建单个柱 CadQuery 几何体.

        Args:
            cq: CadQuery 模块
            col: 柱数据

        Returns:
            CadQuery Workplane
        """
        cw = col.get("width", 300)
        cd = self.column_depth
        ch = col.get("height", 2400)
        cx = col.get("position_x", 0)

        return (
            cq.Workplane("XY")
            .box(cw, cd, ch)
            .translate((cx, 0, ch / 2))
        )

    def _create_footing_cq(self, cq, col: dict[str, Any]) -> Any:
        """创建单个基础 CadQuery 几何体.

        Args:
            cq: CadQuery 模块
            col: 柱数据

        Returns:
            CadQuery Workplane
        """
        fb = self.foundation.get("base_length", 1200)
        fh = self.foundation.get("height", 500)
        cx = col.get("position_x", 0)

        return (
            cq.Workplane("XY")
            .box(fb, fb, fh)
            .translate((cx, 0, -fh / 2))
        )

    def export_to_stl(self, filepath: str) -> bool:
        """导出3D模型为 STL 格式.

        Args:
            filepath: 输出路径

        Returns:
            导出成功返回 True，否则 False
        """
        try:
            import cadquery as cq  # type: ignore[import-untyped]

            model = self.generate_3d_model()
            if model:
                cq.exporters.export(model, filepath)
                logger.info(f"STL 导出成功: {filepath}")
                return True
            return False
        except Exception as e:
            logger.error(f"STL 导出失败: {e}")
            return False

    def get_bounding_box(self) -> dict[str, float]:
        """获取模型包围盒尺寸.

        Returns:
            包围盒尺寸字典 {length, height, depth}
        """
        wall_length = 0.0
        wall_height = 0.0

        panels = self.modular.get("total_panels", [])
        if panels:
            max_x = max(
                p.get("position_x", 0) + p.get("width", 0) / 2 for p in panels
            )
            wall_length = max_x

        columns = self.modular.get("columns", [])
        if columns:
            wall_height = max(c.get("height", 2400) for c in columns)

        return {
            "length": wall_length,
            "height": wall_height,
            "depth": self.column_depth,
        }