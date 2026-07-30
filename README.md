# AKO_Wall_Designer_Agent

## 围墙设计智能体

面向**装配式围墙设计**的AI智能体（Agent），通过自然语言交互，实现从**设计条件输入** → **结构计算** → **草图生成** → **效果图渲染**的全链路自动化设计。

系统定位为建筑师与结构工程师的AI协作者。

## 快速开始

```bash
# 克隆项目
git clone <repo-url>
cd AKO_Wall_Designer_Agent

# 安装依赖
poetry install

# 配置环境变量
cp .env.example .env
# 编辑 .env 填入 API Key

# 启动 Gradio 界面
python src/main.py
```

## 核心能力

| 能力域 | 具体功能 | 技术实现 |
| :--- | :--- | :--- |
| **参数解析** | 自然语言→结构化设计参数 | LLM Function Calling |
| **模数计算** | 基于600mm模数的墙板排布与柱位优化 | 确定性规则引擎 |
| **结构设计** | 混凝土柱/钢柱断面、配筋/选型、基础设计 | 规范公式 + 截面库 |
| **几何生成** | 精确3D模型、2D线稿、深度图 | CadQuery |
| **草图生成** | 手绘风格线稿 + 尺寸标注 | ControlNet-Lineart + SD |
| **效果图渲染** | 逼真材质 + 环境光照 | SDXL + ControlNet + LoRA |
| **报告输出** | 结构计算书 + 材料清单 | Markdown/PDF生成 |

## 项目结构

```
AKO_Wall_Designer_Agent/
├── pyproject.toml
├── src/
│   ├── main.py
│   ├── agents/          # LangGraph 编排
│   ├── parsers/         # 参数解析
│   ├── calculators/     # 模数计算
│   ├── structural/      # 结构设计
│   ├── geometry/        # 几何生成
│   ├── sketch/          # 草图生成
│   ├── render/          # 效果图生成
│   ├── reports/         # 报告生成
│   ├── materials/       # 材质库
│   ├── ui/              # Gradio 界面
│   └── utils/           # 工具函数
├── data/                # 数据文件
├── tests/               # 测试
├── models/              # 模型文件
├── outputs/             # 输出目录
└── scripts/             # 辅助脚本
```

## 技术栈

- **Python 3.11+**
- **LangGraph** - Agent 状态机编排
- **OpenAI/Anthropic** - 自然语言参数解析
- **CadQuery** - 精确3D建模
- **Stable Diffusion XL + ControlNet + LoRA** - 效果图与草图生成
- **Gradio** - Web 交互界面
- **Pydantic** - 数据验证

## 设计规范依据

- GB 50009-2012《建筑结构荷载规范》
- GB 50010-2010《混凝土结构设计规范》
- GB 50017-2017《钢结构设计标准》
- GB 50007-2011《建筑地基基础设计规范》
- GB 50011-2010《建筑抗震设计规范》

## License

Proprietary - AKO Design Lab
---
> 作者：AKO_studio
> 日期：2026-07-30
