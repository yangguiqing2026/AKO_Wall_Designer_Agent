"""Gradio UI 组件模块."""

from typing import Any

import gradio as gr


def build_input_panel() -> list[Any]:
    """构建输入面板组件.

    Returns:
        Gradio 组件列表
    """
    with gr.Column():
        gr.Markdown("## 🏗️ 围墙设计智能体")
        gr.Markdown("请输入您的围墙设计需求，AI 将自动完成参数解析、结构计算和效果图生成。")

        # 自然语言输入
        description = gr.Textbox(
            label="设计需求描述",
            placeholder="例如: 设计一段50米长的清水混凝土围墙，高度2.4米，柱间距3.6米，用于深圳地区...",
            lines=5,
            max_lines=10,
        )

        with gr.Row():
            with gr.Column(scale=1):
                # 快速参数调整
                wall_length = gr.Number(
                    label="围墙总长度 (mm)", value=50000, minimum=1000, precision=0
                )
                wall_height = gr.Number(
                    label="围墙总高度 (mm)", value=2400, minimum=1200, precision=0
                )
                column_spacing = gr.Number(
                    label="扶壁柱间距 (mm)", value=3600, minimum=1000, precision=0
                )

            with gr.Column(scale=1):
                column_material = gr.Dropdown(
                    label="扶壁柱材质",
                    choices=["concrete", "steel", "steel_corten"],
                    value="concrete",
                )
                surface_finish = gr.Dropdown(
                    label="表面饰面",
                    choices=["fair-faced", "wood-grain", "rustic"],
                    value="fair-faced",
                )
                seismic_intensity = gr.Slider(
                    label="抗震设防烈度",
                    minimum=6,
                    maximum=9,
                    value=6,
                    step=1,
                )

            with gr.Column(scale=1):
                terrain_category = gr.Dropdown(
                    label="地面粗糙度",
                    choices=["A", "B", "C", "D"],
                    value="C",
                )
                wind_pressure = gr.Number(
                    label="基本风压 (kN/m²)",
                    value=None,
                    precision=2,
                )
                panel_width = gr.Number(
                    label="标准板宽 (mm)", value=600, minimum=300, maximum=1200, precision=0
                )

        submit_btn = gr.Button("🚀 开始设计", variant="primary", size="lg")

    return [
        description,
        wall_length,
        wall_height,
        column_spacing,
        column_material,
        surface_finish,
        seismic_intensity,
        terrain_category,
        wind_pressure,
        panel_width,
        submit_btn,
    ]


def build_output_panel() -> list[Any]:
    """构建输出面板组件.

    Returns:
        Gradio 组件列表
    """
    with gr.Column():
        gr.Markdown("## 📊 设计结果")

        status = gr.Textbox(label="处理状态", value="等待输入...", interactive=False)

        with gr.Tabs():
            with gr.TabItem("📐 立面草图"):
                sketch_image = gr.Image(label="立面草图", type="pil")

            with gr.TabItem("🎨 彩色效果图"):
                render_image = gr.Image(label="效果图", type="pil")

            with gr.TabItem("📋 结构计算书"):
                report_md = gr.Markdown("计算书将在设计完成后显示...")

            with gr.TabItem("📦 材料清单"):
                material_json = gr.JSON(label="材料清单", value=None)

            with gr.TabItem("📄 参数确认"):
                params_json = gr.JSON(label="解析参数", value=None)

    return [status, sketch_image, render_image, report_md, material_json, params_json]


def build_simple_ui() -> gr.Blocks:
    """构建完整的 Gradio 界面.

    Returns:
        Gradio Blocks 界面
    """
    with gr.Blocks(
        title="AKO Wall Designer Agent",
        theme=None,
        css="""
        .main-container { max-width: 1400px; margin: auto; }
        .output-area { min-height: 400px; }
        """,
    ) as app:
        gr.HTML(
            """
            <div style="text-align: center; margin: 1em 0;">
                <h1>🏗️ AKO_Wall_Designer_Agent</h1>
                <p style="color: #666;">装配式围墙设计智能体 - 从概念到图纸的全链路AI设计</p>
            </div>
            """
        )

        # 输入区域
        inputs = build_input_panel()

        # 输出区域
        outputs = build_output_panel()

        # 绑定事件
        input_description = inputs[0]
        submit_btn = inputs[-1]
        status = outputs[0]

        def update_status(msg: str) -> str:
            return msg

        submit_btn.click(
            fn=update_status,
            inputs=[gr.Textbox(value="正在处理...", visible=False)],
            outputs=[status],
        )

    return app