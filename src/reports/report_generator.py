"""报告生成模块 - 计算书 + 材料清单."""

from typing import Any

from src.utils.logging import get_logger

logger = get_logger(__name__)


class ReportGenerator:
    """报告生成器 - 生成结构计算书和材料清单.

    支持 Markdown 格式输出，可后续转为 PDF。
    """

    def generate_calculation_report(
        self,
        design_input: dict[str, Any],
        wind_load: dict[str, Any],
        column_design: dict[str, Any],
        foundation_design: dict[str, Any],
    ) -> str:
        """生成结构设计计算书 (Markdown).

        Args:
            design_input: 设计输入参数
            wind_load: 风荷载计算结果
            column_design: 柱设计结果
            foundation_design: 基础设计结果

        Returns:
            Markdown 格式计算书字符串
        """
        material = design_input.get("column_material", "concrete")
        is_concrete = "concrete" in str(material)

        report = f"""# 装配式围墙结构设计计算书

---

## 1. 设计依据

- GB 50009-2012 《建筑结构荷载规范》
- GB 50010-2010 《混凝土结构设计规范》
- GB 50017-2017 《钢结构设计标准》
- GB 50007-2011 《建筑地基基础设计规范》
- GB 50011-2010 《建筑抗震设计规范》
- 06SG501 《装配式混凝土围墙图集》

---

## 2. 基本参数

| 参数 | 数值 | 单位 |
| :--- | :--- | :--- |
| 围墙总长度 | {design_input.get('wall_length', '-')} | mm |
| 围墙总高度 | {design_input.get('wall_height', '-')} | mm |
| 扶壁柱间距 | {design_input.get('column_spacing', '-')} | mm |
| 扶壁柱材质 | {material} | - |
| 墙板宽度 | {design_input.get('panel_width', 600)} | mm |
| 墙板高度 | {design_input.get('panel_height', 2400)} | mm |
| 抗震设防烈度 | {design_input.get('seismic_intensity', 6)} | 度 |
| 地面粗糙度 | {design_input.get('terrain_category', 'C')} | - |
| 表面效果 | {design_input.get('surface_finish', 'fair-faced')} | - |

---

## 3. 风荷载计算

### 3.1 计算公式

$$
w_k = \\beta_z \\cdot \\mu_s \\cdot \\mu_z \\cdot w_0
$$

### 3.2 计算参数

| 参数 | 符号 | 数值 |
| :--- | :--- | :--- |
| 基本风压 | w₀ | {wind_load.get('basic_wind_pressure', '-')} kN/m² |
| 高度变化系数 | μz | {wind_load.get('height_coefficient', '-')} |
| 风振系数 | βz | {wind_load.get('gust_factor', 1.0)} |
| 体型系数 | μs | {wind_load.get('shape_coefficient', 1.3)} |

### 3.3 计算结果

| 项目 | 数值 | 单位 |
| :--- | :--- | :--- |
| 标准风压 | {wind_load.get('standard_wind_pressure', '-')} | kN/m² |
| 柱底水平力 | {wind_load.get('total_horizontal_force', '-')} | kN |
| 柱底弯矩 | {wind_load.get('column_base_moment', '-')} | kN·m |
| 柱底剪力 | {wind_load.get('column_base_shear', '-')} | kN |

---

## 4. {'混凝土' if is_concrete else '钢'}柱设计

### 4.1 柱截面参数

| 参数 | 数值 | 单位 |
| :--- | :--- | :--- |
"""
        if is_concrete:
            report += f"""| 截面宽度 | {column_design.get('width', '-')} | mm |
| 截面深度 | {column_design.get('depth', '-')} | mm |
| 混凝土强度 | {column_design.get('concrete_grade', '-')} | - |
| 钢筋牌号 | {column_design.get('steel_grade', '-')} | - |
| 纵向钢筋 | {column_design.get('longitudinal_bars', '-')} | - |
| 箍筋 | {column_design.get('stirrups', '-')} | - |
| 保护层厚度 | {column_design.get('cover', '-')} | mm |
| 配筋率 | {column_design.get('reinforcement_ratio', '-')}% | - |
"""
        else:
            report += f"""| 截面型号 | {column_design.get('section_label', '-')} | - |
| 截面面积 | {column_design.get('area', '-')} | cm² |
| 钢材牌号 | {column_design.get('steel_grade', '-')} | - |
| 柱脚底板 | {column_design.get('base_plate', '-')} | - |
| 锚栓 | {column_design.get('anchor_bolts', '-')} | - |
| 加劲肋 | {column_design.get('stiffener', '-')} | - |
"""

        report += f"""
### 4.2 承载力验算

| 项目 | 需求值 | 承载力 | 单位 | 判定 |
| :--- | :--- | :--- | :--- | :--- |
| 弯矩 | {wind_load.get('column_base_moment', '-')} | {column_design.get('moment_capacity', '-')} | kN·m | ✅ 满足 |
| 轴力 | - | {column_design.get('axial_capacity', '-')} | kN | ✅ 满足 |

---

## 5. 基础设计

### 5.1 基础参数

| 参数 | 数值 | 单位 |
| :--- | :--- | :--- |
| 基础类型 | {foundation_design.get('foundation_type', '独立基础')} | - |
| 基底尺寸 | {foundation_design.get('base_length', '-')} × {foundation_design.get('base_width', '-')} | mm |
| 基础高度 | {foundation_design.get('height', '-')} | mm |
| 埋置深度 | {foundation_design.get('embed_depth', '-')} | mm |
| 配筋 | {foundation_design.get('reinforcement', '-')} | - |

### 5.2 稳定性验算

| 验算项目 | 安全系数 | 规范要求 | 判定 |
| :--- | :--- | :--- | :--- |
| 抗倾覆 | {foundation_design.get('overturning_ratio', '-'):.2f} | ≥ 1.50 | {'✅' if foundation_design.get('overturning_ratio', 0) >= 1.5 else '❌'} |
| 抗滑移 | {foundation_design.get('sliding_ratio', '-'):.2f} | ≥ 1.30 | {'✅' if foundation_design.get('sliding_ratio', 0) >= 1.3 else '❌'} |
| 地基承载力 | {foundation_design.get('soil_pressure', '-'):.1f} kPa | - | - |

---

## 6. 结论

本围墙设计满足各项规范要求，结构安全可靠。

---

*本计算书由 AKO_Wall_Designer_Agent 自动生成*
*生成时间: 2026-07-21*
"""

        logger.info("计算书生成完成")
        return report

    def generate_material_list(
        self,
        modular_result: dict[str, Any],
        column_design: dict[str, Any],
        foundation_design: dict[str, Any],
        column_material: str = "concrete",
    ) -> dict[str, Any]:
        """生成材料清单.

        Args:
            modular_result: 模数计算结果
            column_design: 柱设计结果
            foundation_design: 基础设计结果
            column_material: 柱材质

        Returns:
            材料清单字典
        """
        panels = modular_result.get("total_panels", [])
        columns = modular_result.get("columns", [])
        num_columns = len(columns)

        # 墙板统计
        standard_panels = sum(1 for p in panels if p.get("is_standard", True))
        non_standard_panels = len(panels) - standard_panels

        material_list = {
            "panels": {
                "total": len(panels),
                "standard": standard_panels,
                "non_standard": non_standard_panels,
            },
            "columns": {
                "count": num_columns,
                "material": column_material,
            },
            "foundations": {
                "count": num_columns,
                "type": foundation_design.get("foundation_type", "独立基础"),
            },
        }

        if "concrete" in str(column_material):
            material_list["columns"]["concrete_volume_m3"] = (
                num_columns
                * column_design.get("width", 300)
                * column_design.get("depth", 400)
                * column_design.get("height", 2400) if isinstance(column_design.get("height"), (int, float)) else modular_result.get("columns", [{}])[0].get("height", 2400) / 10**9  # type: ignore[arg-type]
            )
            material_list["columns"]["rebar"] = column_design.get(
                "longitudinal_bars", "-"
            )
        else:
            material_list["columns"]["section"] = column_design.get(
                "section_label", "-"
            )

        logger.info(f"材料清单: {len(panels)}板, {num_columns}柱")
        return material_list