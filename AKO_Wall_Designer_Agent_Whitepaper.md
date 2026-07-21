好的，我直接给您**一份完整的Markdown源码**，一次性复制到VSCode保存为 `.md` 文件即可。

---

```markdown
# AKO_Wall_Designer_Agent

## 围墙设计智能体 · 技术白皮书

**版本**: v1.0  
**日期**: 2026-07-21  
**状态**: 开发基线  
**文档编号**: AKO-WDA-2026-001  
**作者**: AKO Design Lab  

---

## 目录

- [1. 项目概述](#1-项目概述)
- [2. 系统架构设计](#2-系统架构设计)
- [3. 核心模块详解](#3-核心模块详解)
- [4. 技术栈选型](#4-技术栈选型)
- [5. 开发规范与代码结构](#5-开发规范与代码结构)
- [6. API接口设计](#6-api接口设计)
- [7. 数据模型定义](#7-数据模型定义)
- [8. 工作流引擎](#8-工作流引擎)
- [9. 验收标准与测试策略](#9-验收标准与测试策略)
- [10. 部署与运维](#10-部署与运维)
- [11. 开发路线图](#11-开发路线图)
- [12. 附录](#12-附录)

---

## 1. 项目概述

### 1.1 项目定位

AKO_Wall_Designer_Agent 是一款面向**装配式围墙设计**的智能体（Agent），通过自然语言交互，实现从**设计条件输入** → **结构计算** → **草图生成** → **效果图渲染**的全链路自动化设计。系统定位为建筑师与结构工程师的AI协作者。

### 1.2 核心能力矩阵

| 能力域 | 具体功能 | 技术实现 |
| :--- | :--- | :--- |
| **参数解析** | 自然语言→结构化设计参数 | LLM Function Calling |
| **模数计算** | 基于600mm模数的墙板排布与柱位优化 | 确定性规则引擎 |
| **结构设计** | 混凝土柱/钢柱断面、配筋/选型、基础设计 | 规范公式 + 截面库 |
| **几何生成** | 精确3D模型、2D线稿、深度图 | CadQuery |
| **草图生成** | 手绘风格线稿 + 尺寸标注 | ControlNet-Lineart + SD |
| **效果图渲染** | 逼真材质 + 环境光照 | SDXL + ControlNet + LoRA |
| **报告输出** | 结构计算书 + 材料清单 | Markdown/PDF生成 |

### 1.3 设计输入参数清单

| 参数 | 类型 | 单位 | 必填 | 默认值 | 说明 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `wall_length` | float | mm | ✅ | - | 围墙总长度 |
| `wall_height` | float | mm | ✅ | - | 围墙总高度 |
| `column_spacing` | float | mm | ✅ | - | 扶壁柱间距 |
| `column_material` | enum | - | ✅ | - | 混凝土/钢柱/耐候钢 |
| `panel_width` | float | mm | ❌ | 600 | 标准墙板宽度 |
| `panel_height` | float | mm | ❌ | 2400 | 标准墙板高度 |
| `column_width` | float | mm | ❌ | 自动 | 柱宽，不填自动计算 |
| `wind_pressure` | float | kN/m² | ❌ | 查表 | 基本风压 |
| `terrain_category` | enum | - | ❌ | "C" | 地面粗糙度A/B/C/D |
| `surface_finish` | string | - | ❌ | "fair-faced" | 表面效果 |
| `seismic_intensity` | int | 度 | ❌ | 6 | 抗震设防烈度(6-9) |

### 1.4 输出物清单

| 输出物 | 格式 | 说明 |
| :--- | :--- | :--- |
| 参数确认报告 | JSON / Markdown | 解析后的结构化参数确认 |
| 结构设计计算书 | Markdown / PDF | 含荷载计算、公式、验算过程 |
| 立面草图 | PNG / SVG | 线稿 + 尺寸标注 + 柱位 |
| 平面草图 | PNG / SVG | 柱位 + 基础轮廓 |
| 剖面大样 | PNG / SVG | 柱-墙节点 + 基础剖面 |
| 彩色效果图 | PNG (2048×1536) | 逼真材质渲染 + 环境光照 |
| 材料清单 | JSON / CSV | 板、柱、钢筋/型钢数量统计 |
| 3D模型 | STL / OBJ | 精确几何模型 |

---

## 2. 系统架构设计

### 2.1 整体架构图（五层架构）

```
┌─────────────────────────────────────────────────────────────────────┐
│                      用户交互层 (UI Layer)                         │
│  ┌─────────────────┐  ┌─────────────────┐  ┌───────────────────┐  │
│  │   Gradio Web    │  │   CLI 接口      │  │   REST API        │  │
│  │   (主交互界面)   │  │   (调试/批处理)  │  │   (外部集成)      │  │
│  └─────────────────┘  └─────────────────┘  └───────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   智能体编排层 (Orchestration Layer)               │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │              LangGraph 状态机 (StateGraph)                  │  │
│  │  解析 → 计算 → 结构设计 → 草图 → 效果图 → 报告 → 输出     │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    核心服务层 (Core Services)                      │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────────────┐  │
│  │ 参数解析      │  │ 模数计算      │  │ 结构设计                │  │
│  │ Service      │  │ Service      │  │ Service                 │  │
│  └──────────────┘  └──────────────┘  └─────────────────────────┘  │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────────────┐  │
│  │ 几何生成      │  │ 草图生成      │  │ 效果图生成              │  │
│  │ Service      │  │ Service      │  │ Service                 │  │
│  └──────────────┘  └──────────────┘  └─────────────────────────┘  │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────────────┐  │
│  │ 材质库        │  │ 报告生成      │  │ 文件管理                │  │
│  │ Service      │  │ Service      │  │ Service                 │  │
│  └──────────────┘  └──────────────┘  └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    基础设施层 (Infrastructure)                     │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────────────┐  │
│  │   LLM API    │  │   SDXL       │  │   CadQuery              │  │
│  │  (OpenAI)    │  │  (Local GPU) │  │   引擎                   │  │
│  └──────────────┘  └──────────────┘  └─────────────────────────┘  │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────────────┐  │
│  │   ControlNet │  │   LoRA       │  │   文件存储               │  │
│  │   模型集      │  │   模型集     │  │   (Local/S3)            │  │
│  └──────────────┘  └──────────────┘  └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    数据层 (Data Layer)                             │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────────────┐  │
│  │   规范库      │  │   材料库      │  │   案例库                 │  │
│  │   (JSON)     │  │   (JSON)     │  │   (JSON)                │  │
│  └──────────────┘  └──────────────┘  └─────────────────────────┘  │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────────────┐  │
│  │   截面库      │  │   LoRA权重   │  │   用户会话               │  │
│  │   (JSON)     │  │   (.safetensors)│  │   (SQLite)             │  │
│  └──────────────┘  └──────────────┘  └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.2 数据流图

```
用户输入 → LangGraph State → 参数解析器 → 模数计算器 → 结构设计器
    → 几何生成器 → 草图生成器 → 效果图生成器 → 报告生成器 → 输出聚合 → 用户输出

规范库 ⇄ 模数计算器 / 结构设计器
截面库 ⇄ 结构设计器
材质LoRA库 ⇄ 效果图生成器
```

---

## 3. 核心模块详解

### 3.1 参数解析模块 (Parameter Parser)

**职责**: 将用户自然语言输入转换为结构化设计参数

**技术方案**: LLM Function Calling + Pydantic 校验

```python
# src/parsers/parameter_parser.py
from pydantic import BaseModel, Field, validator
from enum import Enum
from typing import Optional

class ColumnMaterial(str, Enum):
    CONCRETE = "concrete"
    STEEL = "steel"
    STEEL_CORTEN = "steel_corten"

class TerrainCategory(str, Enum):
    A = "A"  # 近海海面、海岛、海岸
    B = "B"  # 田野、乡村、丘陵
    C = "C"  # 有密集建筑群的城市市区
    D = "D"  # 有密集建筑群且房屋较高的城市市区

class DesignInput(BaseModel):
    wall_length: float = Field(..., gt=0, description="围墙总长度(mm)")
    wall_height: float = Field(..., gt=0, description="围墙总高度(mm)")
    column_spacing: float = Field(..., gt=0, description="扶壁柱间距(mm)")
    column_material: ColumnMaterial = Field(..., description="扶壁柱材质")
    panel_width: float = Field(600, ge=300, le=1200, description="墙板宽度(mm)")
    panel_height: float = Field(2400, ge=1200, le=3600, description="墙板高度(mm)")
    column_width: Optional[float] = Field(None, description="柱宽(mm)，不填则自动计算")
    wind_pressure: Optional[float] = Field(None, description="基本风压(kN/m²)")
    terrain_category: TerrainCategory = Field(TerrainCategory.C, description="地面粗糙度")
    surface_finish: str = Field("fair-faced", description="表面效果")
    seismic_intensity: int = Field(6, ge=6, le=9, description="抗震设防烈度")

    @validator('column_width', always=True)
    def set_default_column_width(cls, v, values):
        if v is None:
            material = values.get('column_material')
            if material == ColumnMaterial.CONCRETE:
                return 300
            else:
                return 250
        return v
```

### 3.2 模数计算模块 (Modular Calculation)

**职责**: 基于600mm模数计算墙板排布、柱位、非标段处理

```python
# src/calculators/modular_calculator.py
from dataclasses import dataclass
from typing import List

@dataclass
class Panel:
    width: float
    height: float
    is_standard: bool
    position_x: float
    position_y: float
    layer_index: int

@dataclass
class Column:
    width: float
    depth: float
    height: float
    position_x: float
    material: str
    index: int

@dataclass
class ModularResult:
    panels_per_span: int
    actual_spacing: float
    num_spans: int
    total_panels: List[Panel]
    columns: List[Column]
    remainder: float
    total_height_layers: int
    actual_wall_height: float
    is_height_adjusted: bool
    adjustment_message: str
    non_standard_panels: List[Panel]
```

**非标段处理策略**:

| 剩余长度 | 处理策略 |
| :--- | :--- |
| 0 | 完美匹配，无特殊处理 |
| < 300mm | 并入相邻段，微调相邻柱距 |
| 300 ~ 1200mm | 生成非标板，居中或端部放置 |
| > 1200mm | 建议用户调整总长度或柱距 |

### 3.3 结构设计模块 (Structural Design)

**职责**: 根据材质、荷载、几何参数计算柱断面、配筋/选型、基础尺寸

#### 3.3.1 风荷载计算 (GB 50009-2012)

```python
# src/structural/wind_load.py

def calculate_wind_load(height: float, spacing: float,
                        terrain: TerrainCategory,
                        wind_pressure: float) -> dict:
    """计算作用于扶壁柱顶部的水平力"""
    # 风压高度变化系数 μz
    mu_z = get_height_coefficient(height, terrain)
    # 风振系数 βz (围墙可取1.0)
    beta_z = 1.0
    # 体型系数 μs (围墙取1.3)
    mu_s = 1.3
    # 标准风压 wk = βz * μs * μz * w0
    wk = beta_z * mu_s * mu_z * wind_pressure
    # 单柱受荷宽度 = 柱间距
    tributary_width = spacing / 1000
    # 柱底弯矩
    total_force = wk * tributary_width * height
    moment = total_force * height / 2

    return {
        "standard_wind_pressure": wk,
        "total_horizontal_force": total_force,
        "column_base_moment": moment,
        "column_base_shear": total_force,
    }
```

#### 3.3.2 混凝土柱设计

```python
# src/structural/concrete_column.py
from dataclasses import dataclass

@dataclass
class ConcreteColumnDesign:
    width: int
    depth: int
    concrete_grade: str
    steel_grade: str
    longitudinal_bars: str
    longitudinal_bars_area: float
    stirrups: str
    stirrups_zone: str
    cover: int
    axial_capacity: float
    moment_capacity: float
    reinforcement_ratio: float
```

**典型输出**:
- 柱截面: 300×400 mm
- 混凝土强度等级: C30
- 纵向钢筋: 4Φ20 (HRB400)
- 箍筋: Φ8@150 (加密区 Φ8@100)
- 配筋率: 0.85%

#### 3.3.3 钢柱设计 (Q355B)

```python
# src/structural/steel_column.py
from dataclasses import dataclass

@dataclass
class SteelColumnDesign:
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
```

**H型钢截面库（部分）**:

| 型号 | 面积 (cm²) | ix (cm) | iy (cm) | Wx (cm³) |
| :--- | :--- | :--- | :--- | :--- |
| HW150×150 | 40.55 | 6.39 | 3.75 | 221 |
| HW175×175 | 51.43 | 7.50 | 4.38 | 327 |
| HW200×200 | 63.53 | 8.61 | 5.02 | 472 |
| HW250×250 | 92.18 | 10.80 | 6.29 | 862 |
| HW300×300 | 120.40 | 13.10 | 7.61 | 1360 |

**典型输出**:
- 截面型号: HW200×200×8×12
- 钢材牌号: Q355B
- 柱脚底板: -20×400×400
- 锚栓: 4-M24

#### 3.3.4 基础设计

```python
# src/structural/foundation.py
from dataclasses import dataclass

@dataclass
class FoundationDesign:
    type: str
    base_length: int
    base_width: int
    height: int
    embed_depth: int
    reinforcement: str
    soil_pressure: float
    overturning_ratio: float
    sliding_ratio: float
```

**典型输出**:
- 基础类型: 独立基础
- 基底尺寸: 1200×1200 mm
- 基础高度: 500 mm
- 埋置深度: 800 mm
- 配筋: Φ12@150 (双向)
- 抗倾覆安全系数: 2.35
- 抗滑移安全系数: 1.82

### 3.4 几何生成模块 (Geometry Generation)

**职责**: 使用CadQuery生成精确的3D模型、2D线稿、深度图

```python
# src/geometry/wall_generator.py
import cadquery as cq

class WallGeometryGenerator:
    def __init__(self, modular_result, column_design, foundation_design):
        self.modular = modular_result
        self.column = column_design
        self.foundation = foundation_design
        self.panel_thickness = 200
        self.column_depth = 400

    def generate_3d_model(self) -> cq.Workplane:
        model = cq.Workplane("XY")
        for panel in self.modular.total_panels:
            model = model.add(self._create_panel(panel))
        for col in self.modular.columns:
            model = model.add(self._create_column(col))
        for col in self.modular.columns:
            model = model.add(self._create_footing(col))
        return model

    def _create_panel(self, panel: Panel) -> cq.Workplane:
        return cq.Workplane("XY").box(
            panel.width, panel.height, self.panel_thickness
        ).translate((panel.position_x, 0, panel.position_y))

    def _create_column(self, col: Column) -> cq.Workplane:
        return cq.Workplane("XY").box(
            col.width, self.column_depth, col.height
        ).translate((col.position_x, 0, 0))

    def _create_footing(self, col: Column) -> cq.Workplane:
        b = self.foundation.base_length
        h = self.foundation.height
        return cq.Workplane("XY").box(b, b, h).translate(
            (col.position_x, 0, -h)
        )

    def export_to_stl(self, filepath: str):
        model = self.generate_3d_model()
        cq.exporters.export(model, filepath)
```

### 3.5 草图生成模块 (Sketch Generation)

**职责**: 将几何线稿转化为手绘风格草图

```python
# src/sketch/sketch_generator.py
from diffusers import StableDiffusionPipeline, ControlNetModel

class SketchGenerator:
    def __init__(self, device: str = "cuda"):
        self.controlnet = ControlNetModel.from_pretrained(
            "lllyasviel/sd-controlnet-lineart"
        )
        self.pipe = StableDiffusionPipeline.from_pretrained(
            "runwayml/stable-diffusion-v1-5",
            controlnet=self.controlnet
        ).to(device)

    def generate(self, lineart_image, with_dimensions=True):
        prompt = "architectural sketch, hand-drawn pencil style, white background, clean linework, technical drawing, no color, no shading"
        negative = "photorealistic, color, texture, shading, blurry, messy"
        result = self.pipe(
            prompt=prompt,
            negative_prompt=negative,
            image=lineart_image,
            num_inference_steps=30,
            controlnet_conditioning_scale=0.8
        ).images[0]
        if with_dimensions:
            result = self._overlay_dimensions(result)
        return result
```

### 3.6 效果图生成模块 (Render Generation)

**职责**: 生成逼真的彩色效果图，区分混凝土与钢柱材质

```python
# src/render/render_generator.py
from diffusers import StableDiffusionXLPipeline, ControlNetModel

class RenderGenerator:
    def __init__(self, device: str = "cuda"):
        self.pipe = StableDiffusionXLPipeline.from_pretrained(
            "stabilityai/stable-diffusion-xl-base-1.0"
        ).to(device)
        self.depth_cn = ControlNetModel.from_pretrained(
            "lllyasviel/sd-controlnet-depth"
        )
        self.canny_cn = ControlNetModel.from_pretrained(
            "lllyasviel/sd-controlnet-canny"
        )

    def generate(self, depth_map, mask, params):
        if params.column_material.value in ["concrete"]:
            prompt = self._build_concrete_prompt(params)
            result = self._generate_region(depth_map, mask, prompt, "concrete")
        else:
            prompt = self._build_steel_prompt(params)
            result = self._generate_region(depth_map, mask, prompt, "steel")
        return result
```

### 3.7 材质库模块 (Material Library)

| 材质类型 | 名称 | LoRA权重 | 色温 |
| :--- | :--- | :--- | :--- |
| `concrete_fair` | 清水混凝土 | 0.8 | 中性 |
| `concrete_wood` | 仿木纹混凝土 | 0.7 | 暖色 |
| `concrete_rustic` | 粗犷混凝土 | 0.75 | 中性 |
| `steel_fluoro` | 氟碳喷涂钢柱 | 0.7 | 冷色 |
| `steel_corten` | 耐候钢锈蚀 | 0.8 | 暖色 |

### 3.8 报告生成模块 (Report Generation)

**职责**: 生成结构计算书和材料清单

```python
# src/reports/report_generator.py
class ReportGenerator:
    def generate_calculation_report(self, design_input, wind_load,
                                    column_design, foundation_design) -> str:
        return f"""# 装配式围墙结构设计计算书

## 1. 设计依据
- GB 50009-2012 《建筑结构荷载规范》
- GB 50010-2010 《混凝土结构设计规范》
- GB 50017-2017 《钢结构设计标准》
- GB 50007-2011 《建筑地基基础设计规范》

## 2. 基本参数
| 参数 | 数值 |
| :--- | :--- |
| 围墙总长度 | {design_input.wall_length} mm |
| 围墙总高度 | {design_input.wall_height} mm |
| 扶壁柱间距 | {design_input.column_spacing} mm |
| 扶壁柱材质 | {design_input.column_material.value} |
| 基本风压 | {wind_load['standard_wind_pressure']:.3f} kN/m² |
...
"""
```

---

## 4. 技术栈选型

### 4.1 核心技术栈

| 类别 | 技术 | 版本 | 用途 |
| :--- | :--- | :--- | :--- |
| **语言** | Python | 3.11+ | 主开发语言 |
| **AI框架** | LangGraph | ≥0.2.0 | Agent状态机编排 |
| **LLM** | OpenAI API / Anthropic | - | 参数解析 |
| **图像生成** | Stable Diffusion XL | 1.0 | 效果图生成 |
| **ControlNet** | lllyasviel/controlnet | - | 几何约束生成 |
| **3D几何** | CadQuery | 2.4 | 精确建模 |
| **Web框架** | Gradio | 4.0+ | 交互界面 |
| **数据验证** | Pydantic | 2.0+ | 参数校验 |
| **科学计算** | NumPy / SciPy | - | 结构计算 |
| **依赖管理** | Poetry | - | 包管理 |

### 4.2 模型与权重清单

| 模型 | 来源 | 大小 | 说明 |
| :--- | :--- | :--- | :--- |
| SDXL Base | Stability AI | ~7GB | 基础扩散模型 |
| ControlNet-Depth | lllyasviel | ~1.5GB | 深度约束 |
| ControlNet-Canny | lllyasviel | ~1.5GB | 边缘约束 |
| ControlNet-Lineart | lllyasviel | ~1.5GB | 线稿约束 |
| Concrete LoRA | 自训练 | ~50MB | 混凝土纹理 |
| Steel LoRA | 自训练 | ~50MB | 钢材纹理 |
| IC-Light | lllyasviel | ~2GB | 光照控制 |

### 4.3 开发工具

| 工具 | 用途 |
| :--- | :--- |
| VSCode | 主IDE |
| Python Extension | 代码开发 |
| Jupyter | 原型验证 |
| Git | 版本控制 |
| Docker | 容器化部署 |
| Ruff | 代码检查/格式化 |

---

## 5. 开发规范与代码结构

### 5.1 项目目录结构

```
AKO_Wall_Designer_Agent/
├── pyproject.toml                 # Poetry 依赖管理
├── .env.example                   # 环境变量模板
├── README.md                      # 项目说明
├── docs/
│   ├── whitepaper.md              # 本白皮书
│   ├── api_reference.md           # API文档
│   └── user_manual.md             # 用户手册
├── src/
│   ├── __init__.py
│   ├── main.py                    # 入口文件
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── orchestrator.py        # LangGraph编排
│   │   └── state.py               # 状态定义
│   ├── parsers/
│   │   ├── __init__.py
│   │   ├── parameter_parser.py    # 参数解析
│   │   └── prompt_templates.py    # LLM Prompt模板
│   ├── calculators/
│   │   ├── __init__.py
│   │   ├── modular_calculator.py  # 模数计算
│   │   └── panel_layout.py        # 板排布
│   ├── structural/
│   │   ├── __init__.py
│   │   ├── wind_load.py           # 风荷载
│   │   ├── concrete_column.py     # 混凝土柱
│   │   ├── steel_column.py        # 钢柱
│   │   ├── foundation.py          # 基础设计
│   │   └── section_library.py     # 型钢库
│   ├── geometry/
│   │   ├── __init__.py
│   │   ├── wall_generator.py      # 几何生成
│   │   └── export_utils.py        # 导出工具
│   ├── sketch/
│   │   ├── __init__.py
│   │   ├── sketch_generator.py    # 草图生成
│   │   └── dimension_overlay.py   # 尺寸标注
│   ├── render/
│   │   ├── __init__.py
│   │   ├── render_generator.py    # 效果图生成
│   │   └── regional_control.py    # 区域控制
│   ├── materials/
│   │   ├── __init__.py
│   │   ├── material_library.py    # 材质库
│   │   └── lora_loader.py         # LoRA加载
│   ├── reports/
│   │   ├── __init__.py
│   │   ├── report_generator.py    # 报告生成
│   │   └── templates/              # 报告模板
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── gradio_app.py          # Gradio界面
│   │   └── components.py          # UI组件
│   └── utils/
│       ├── __init__.py
│       ├── config.py              # 配置管理
│       ├── logging.py             # 日志
│       └── file_io.py             # 文件读写
├── tests/
│   ├── __init__.py
│   ├── unit/
│   │   ├── test_parsers/
│   │   ├── test_calculators/
│   │   └── test_structural/
│   └── integration/
│       └── test_workflow.py
├── models/                         # 本地模型存放
│   ├── lora/
│   │   ├── concrete_fair.safetensors
│   │   ├── concrete_wood.safetensors
│   │   ├── steel_fluoro.safetensors
│   │   └── steel_corten.safetensors
│   └── controlnet/
├── data/                           # 数据文件
│   ├── standards/
│   │   ├── wind_pressure.json     # 全国风压数据
│   │   ├── soil_types.json        # 地基类型
│   │   └── seismic_zones.json     # 抗震分区
│   └── examples/                   # 示例输入输出
├── outputs/                        # 运行时输出
│   ├── sketches/
│   ├── renders/
│   └── reports/
└── scripts/
    ├── train_lora.py              # LoRA训练脚本
    └── preprocess_data.py         # 数据预处理
```

### 5.2 命名规范

| 类型 | 规范 | 示例 |
| :--- | :--- | :--- |
| 模块文件 | snake_case | `modular_calculator.py` |
| 类名 | PascalCase | `ModularCalculator` |
| 函数/方法 | snake_case | `calculate_panel_layout()` |
| 变量 | snake_case | `panel_width` |
| 常量 | UPPER_SNAKE | `MAX_PANEL_HEIGHT` |
| 私有方法 | _开头 | `_validate_input()` |

### 5.3 代码质量要求

- **类型注解**: 所有函数必须有完整的类型注解
- **文档字符串**: 所有公共类/方法必须有docstring (Google风格)
- **测试覆盖率**: ≥ 80%
- **代码风格**: 遵循PEP 8, 使用Ruff格式化

---

## 6. API接口设计

### 6.1 内部状态定义 (LangGraph)

```python
# src/agents/state.py
from typing import TypedDict, Optional, Dict, Any
from enum import Enum

class ProcessingStatus(str, Enum):
    PENDING = "pending"
    PARSING = "parsing"
    CALCULATING = "calculating"
    STRUCTURAL_DESIGN = "structural_design"
    GEOMETRY = "geometry"
    SKETCH = "sketch"
    RENDER = "render"
    REPORT = "report"
    COMPLETE = "complete"
    ERROR = "error"

class AgentState(TypedDict, total=False):
    raw_input: str
    parsed_params: Optional[Dict[str, Any]]
    modular_result: Optional[Dict[str, Any]]
    wind_load: Optional[Dict[str, float]]
    column_design: Optional[Dict[str, Any]]
    foundation_design: Optional[Dict[str, Any]]
    sketch_path: Optional[str]
    render_path: Optional[str]
    report_path: Optional[str]
    model_path: Optional[str]
    status: ProcessingStatus
    error_message: Optional[str]
    progress: float
```

### 6.2 REST API (外部集成)

| 端点 | 方法 | 描述 |
| :--- | :--- | :--- |
| `/api/design` | POST | 提交设计任务 |
| `/api/status/{task_id}` | GET | 查询任务状态 |
| `/api/result/{task_id}` | GET | 获取设计结果 |

---

## 7. 数据模型定义

### 7.1 全国风压数据库

```json
{
  "cities": [
    {"name": "北京", "wind_pressure": 0.45, "terrain": "C"},
    {"name": "上海", "wind_pressure": 0.55, "terrain": "B"},
    {"name": "广州", "wind_pressure": 0.50, "terrain": "B"},
    {"name": "深圳", "wind_pressure": 0.75, "terrain": "B"},
    {"name": "成都", "wind_pressure": 0.30, "terrain": "C"},
    {"name": "武汉", "wind_pressure": 0.35, "terrain": "C"},
    {"name": "西安", "wind_pressure": 0.35, "terrain": "C"},
    {"name": "乌鲁木齐", "wind_pressure": 0.60, "terrain": "B"}
  ]
}
```

### 7.2 地基承载力参考

| 土类 | 承载力 (kPa) |
| :--- | :--- |
| 岩石 | ≥ 500 |
| 碎石土 | 200-400 |
| 砂土 (密实) | 200-350 |
| 砂土 (中密) | 150-250 |
| 粘性土 (硬塑) | 180-250 |
| 粘性土 (可塑) | 120-180 |
| 粘性土 (软塑) | 80-120 |
| 填土 | 60-100 |

---

## 8. 工作流引擎

### 8.1 LangGraph 状态图定义

```python
# src/agents/orchestrator.py
from langgraph.graph import StateGraph, END
from src.agents.state import AgentState

class WallDesignerOrchestrator:
    def __init__(self):
        self.graph = StateGraph(AgentState)
        self._build_graph()

    def _build_graph(self):
        self.graph.add_node("parse_input", self.parse_input)
        self.graph.add_node("calculate_modular", self.calculate_modular)
        self.graph.add_node("structural_design", self.structural_design)
        self.graph.add_node("generate_geometry", self.generate_geometry)
        self.graph.add_node("generate_sketch", self.generate_sketch)
        self.graph.add_node("generate_render", self.generate_render)
        self.graph.add_node("generate_report", self.generate_report)

        self.graph.set_entry_point("parse_input")
        self.graph.add_edge("parse_input", "calculate_modular")
        self.graph.add_edge("calculate_modular", "structural_design")
        self.graph.add_edge("structural_design", "generate_geometry")
        self.graph.add_edge("generate_geometry", "generate_sketch")
        self.graph.add_edge("generate_sketch", "generate_render")
        self.graph.add_edge("generate_render", "generate_report")
        self.graph.add_edge("generate_report", END)

        self.agent = self.graph.compile()

    async def run(self, user_input: str) -> Dict:
        initial_state = {"raw_input": user_input}
        result = await self.agent.ainvoke(initial_state)
        return result
```

---

## 9. 验收标准与测试策略

### 9.1 功能验收标准

| 编号 | 验收项 | 标准 |
| :--- | :--- | :--- |
| F-01 | 参数解析 | 自然语言输入可正确提取所有设计参数 |
| F-02 | 模数计算 | 自动匹配600mm模数，非标情况给出提示 |
| F-03 | 结构设计 | 输出合理的柱断面、配筋/选型、基础尺寸 |
| F-04 | 几何生成 | 导出模型尺寸与设计参数一致 |
| F-05 | 草图生成 | 线稿清晰，标注准确，风格一致 |
| F-06 | 效果图生成 | 材质逼真，柱/墙区分明显 |
| F-07 | 报告生成 | 计算书完整，公式正确 |

### 9.2 性能指标

| 指标 | 目标值 | 测量方式 |
| :--- | :--- | :--- |
| 参数解析时间 | < 3s | API调用计时 |
| 结构计算时间 | < 1s | 本地计算计时 |
| 草图生成时间 | < 10s | GPU推理计时 |
| 效果图生成时间 | < 30s | GPU推理计时 |
| 端到端总时间 | < 60s | 全流程计时 |
| 显存占用 | < 12GB | 峰值检测 |

### 9.3 测试策略

| 测试层级 | 工具 | 覆盖率目标 |
| :--- | :--- | :--- |
| 单元测试 | pytest | ≥ 80% |
| 集成测试 | pytest + mock | 关键流程100% |
| 端到端测试 | 手动 + 脚本 | 5个典型场景 |
| 性能测试 | time + memory_profiler | 满足性能指标 |

---

## 10. 部署与运维

### 10.1 硬件要求

| 组件 | 最低配置 | 推荐配置 |
| :--- | :--- | :--- |
| CPU | 8核心 | 16核心 |
| GPU | 12GB VRAM (NVIDIA) | 24GB VRAM (NVIDIA) |
| RAM | 32GB | 64GB |
| 存储 | 100GB SSD | 200GB NVMe |

### 10.2 环境变量

```bash
# .env 示例
OPENAI_API_KEY=sk-xxx
ANTHROPIC_API_KEY=sk-xxx
MODEL_PATH=./models
OUTPUT_PATH=./outputs
CUDA_VISIBLE_DEVICES=0
LOG_LEVEL=INFO
```

### 10.3 Docker部署

```dockerfile
FROM pytorch/pytorch:2.0.1-cuda11.7-cudnn8-runtime

WORKDIR /app

COPY pyproject.toml poetry.lock ./
RUN pip install poetry && poetry install --no-dev

COPY src/ ./src/
COPY models/ ./models/
COPY data/ ./data/

EXPOSE 7860

CMD ["python", "src/main.py"]
```

---

## 11. 开发路线图

### Phase 1: 核心计算引擎 (Week 1-2)

- [ ] 参数解析模块 (Pydantic模型 + LLM接入)
- [ ] 模数计算模块 (核心算法)
- [ ] 结构设计模块 (风荷载 + 混凝土柱 + 钢柱)

### Phase 2: 几何与图像生成 (Week 3-4)

- [ ] CadQuery几何生成
- [ ] 草图生成 (ControlNet接入)
- [ ] 效果图生成 (SDXL + LoRA)

### Phase 3: 集成与UI (Week 5-6)

- [ ] LangGraph工作流编排
- [ ] Gradio Web界面
- [ ] 报告生成

### Phase 4: 测试与优化 (Week 7-8)

- [ ] 单元测试 + 集成测试
- [ ] 性能优化
- [ ] 模型微调 (LoRA训练)

---

## 12. 附录

### 12.1 参考文献

1. GB 50009-2012. 建筑结构荷载规范
2. GB 50010-2010. 混凝土结构设计规范
3. GB 50017-2017. 钢结构设计标准
4. GB 50007-2011. 建筑地基基础设计规范
5. GB 50011-2010. 建筑抗震设计规范
6. 06SG501. 装配式混凝土围墙图集

### 12.2 缩写表

| 缩写 | 全称 |
| :--- | :--- |
| AI | Artificial Intelligence |
| API | Application Programming Interface |
| CLI | Command Line Interface |
| LoRA | Low-Rank Adaptation |
| LLM | Large Language Model |
| SDXL | Stable Diffusion XL |
| UI | User Interface |

### 12.3 版本历史

| 版本 | 日期 | 变更内容 | 作者 |
| :--- | :--- | :--- | :--- |
| v1.0 | 2026-07-21 | 初始版本发布 | AKO Design Lab |

---

**— 白皮书结束 —**

*本文档为 AKO_Wall_Designer_Agent 项目的技术基线文档，所有开发工作应以此为准。*
```

---

**使用说明**：

1. 在VSCode中新建文件，命名为 `AKO_Wall_Designer_Agent_Whitepaper.md`
2. 将以上全部内容**一次性复制**粘贴到文件中
3. 保存后可使用VSCode的 `Markdown Preview Enhanced` 或内置预览查看排版
4. 如需导出PDF，可使用 `Markdown PDF` 插件或 `pandoc` 转换
