# ============================================
# Author: AKO_studio
# Agent: AKO_wall_designer_agent
# Generated: 2026-07-30
# ============================================
#
"""Gradio Web 应用 — 逐句问询式交互设计向导.

流程:
  1. 逐题问答 (7 个必填参数)
  2. 参数汇总确认
  3. 确认后依次生成: 计算书 → 草图 → 效果图 → 3D模型 → 材料清单
"""

from pathlib import Path
from typing import Any

# [DEPRECATED_GUI] import gradio as gr

from src.agents.step_orchestrator import DesignState, StepOrchestrator
from src.utils.config import Config
from src.utils.logging import get_logger

logger = get_logger(__name__)

CSS = """
.gradio-container { max-width: 1000px !important; margin: auto !important; }
.chat-bubble { padding: 16px 20px; border-radius: 12px; margin: 8px 0; }
.bot-bubble { background: #f0f4ff; }
.confirm-card { background: #f9fafb; border: 2px solid #2563eb; border-radius: 12px; padding: 20px; margin: 16px 0; }
"""

QUESTIONS = [
    {"id": "wall_length", "label": "围墙总长度", "prompt": "请告诉我围墙的总长度（米）",
     "type": "number", "unit": "米", "default": 50,
     "placeholder": "例如: 50"},
    {"id": "wall_height", "label": "围墙总高度", "prompt": "请告诉我围墙的总高度（米）",
     "type": "number", "unit": "米", "default": 2.4,
     "placeholder": "例如: 2.4"},
    {"id": "column_spacing", "label": "扶壁柱间距", "prompt": "请告诉我扶壁柱的间距（米）",
     "type": "number", "unit": "米", "default": 3.6,
     "placeholder": "例如: 3.6"},
    {"id": "column_material", "label": "扶壁柱材质", "prompt": "请选择扶壁柱的材质",
     "type": "choice", "default": "concrete",
     "choices": [("清水混凝土", "concrete"), ("钢柱 (氟碳喷涂)", "steel"), ("耐候钢", "steel_corten")]},
    {"id": "surface_finish", "label": "表面饰面", "prompt": "请选择墙板表面饰面效果",
     "type": "choice", "default": "fair-faced",
     "choices": [("清水混凝土 (素面)", "fair-faced"), ("仿木纹混凝土", "wood-grain"), ("粗犷质感混凝土", "rustic")]},
    {"id": "seismic_intensity", "label": "抗震设防烈度", "prompt": "请选择抗震设防烈度",
     "type": "choice", "default": 6,
     "choices": [("6 度", 6), ("7 度", 7), ("8 度", 8), ("9 度", 9)]},
    {"id": "terrain_category", "label": "地面粗糙度", "prompt": "请选择项目所在地的地面粗糙度类别",
     "type": "choice", "default": "C",
     "choices": [("A 类 — 近海", "A"), ("B 类 — 田野/乡村", "B"), ("C 类 — 城市市区", "C"), ("D 类 — 密集高层", "D")]},
]


class GradioApp:
    def __init__(self, config: Config | None = None):
        self.config = config or Config()
        self.orchestrator = StepOrchestrator(config=self.config)
        self.total_questions = len(QUESTIONS)

    # [DEPRECATED_GUI] def create_interface(self) -> gr.Blocks:
        # [DEPRECATED_GUI] with gr.Blocks(title="AKO Wall Designer") as app:
            # 状态
            answers_state = gr.State({})
            q_index = gr.State(0)

            gr.HTML("""<div style="text-align:center;margin:1em 0;">
                <h1>🏗️ AKO_Wall_Designer_Agent</h1>
                <p style="color:#666;">装配式围墙设计智能体 · 逐句问答式交互</p></div>""")

            # 进度条
            progress_bar = gr.Slider(minimum=0, maximum=self.total_questions, value=0,
                                     label="问答进度", interactive=False)

            # ===== 问答区 =====
            # [DEPRECATED_GUI] bot_msg = gr.Markdown("### 📝 第 1 / 7 题\n\n请告诉我围墙的总长度（米）",
                                  elem_classes=["chat-bubble", "bot-bubble"])
            # [DEPRECATED_GUI] input_text = gr.Textbox(label="请输入", placeholder="例如: 50", visible=True)
            input_choices = gr.Radio(label="请选择", choices=[], visible=False)
            # [DEPRECATED_GUI] with gr.Row():
                # [DEPRECATED_GUI] back_btn = gr.Button("← 上一题", visible=False, size="sm")
                # [DEPRECATED_GUI] next_btn = gr.Button("确认 →", variant="primary")

            # ===== 确认区 =====
            confirm_area = gr.Group(visible=False)
            with confirm_area:
                # [DEPRECATED_GUI] gr.Markdown("### ✅ 参数确认")
                # [DEPRECATED_GUI] confirm_summary = gr.Markdown("")
                # [DEPRECATED_GUI] with gr.Row():
                    # [DEPRECATED_GUI] edit_btn = gr.Button("✏️ 返回修改")
                    # [DEPRECATED_GUI] confirm_btn = gr.Button("🚀 确认并开始生成", variant="primary", size="lg")

            # ===== 结果区 =====
            result_area = gr.Group(visible=False)
            with result_area:
                # [DEPRECATED_GUI] gen_status = gr.Textbox(label="生成状态", interactive=False)
                # [DEPRECATED_GUI] with gr.Tabs():
                    # [DEPRECATED_GUI] with gr.TabItem("📋 计算书"):
                        # [DEPRECATED_GUI] report_view = gr.Markdown("")
                    # [DEPRECATED_GUI] with gr.TabItem("📐 草图"):
                        sketch_view = gr.Image(label="立面草图", type="pil")
                    # [DEPRECATED_GUI] with gr.TabItem("🎨 效果图"):
                        render_view = gr.Image(label="效果图", type="pil")
                    # [DEPRECATED_GUI] with gr.TabItem("📦 材料清单"):
                        material_view = gr.JSON(label="材料清单")
                    # [DEPRECATED_GUI] with gr.TabItem("🔧 3D 模型"):
                        # [DEPRECATED_GUI] stl_view = gr.Textbox(label="STL 模型", interactive=False)

            # ===== 回调 =====

            def _make_question_view(idx: int, answers: dict):
                """生成当前问题的 UI 更新."""
                if idx >= self.total_questions:
                    return _make_confirm_view(answers)

                q = QUESTIONS[idx]
                prompt = f"### 📝 第 {idx + 1} / {self.total_questions} 题\n\n{q['prompt']}"
                is_text = q["type"] == "number"
                is_choice = q["type"] == "choice"

                current = answers.get(q["id"], q["default"])
                text_val = str(current) if is_text and current is not None else ""
                choice_choices = [(l, v) for l, v in q["choices"]] if is_choice else []
                choice_val = current if is_choice else None

                return (
                    gr.update(value=prompt, visible=True),                         # bot_msg
                    gr.update(value=text_val, visible=is_text,
                              placeholder=q.get("placeholder", "")),               # input_text
                    gr.update(value=choice_val, choices=choice_choices,
                              visible=is_choice),                                  # input_choices
                    gr.update(visible=(idx > 0)),                                  # back_btn
                    gr.update(visible=True),                                        # next_btn
                    gr.update(value=idx),                                           # progress_bar
                    gr.update(visible=False),                                       # confirm_area
                    gr.update(value=""),                                            # confirm_summary
                    gr.update(visible=False),                                       # result_area
                )

            def _make_confirm_view(answers: dict):
                """生成确认页 UI 更新."""
                lines = ["| 参数 | 取值 |", "| :--- | :--- |"]
                for q in QUESTIONS:
                    val = answers.get(q["id"], q["default"])
                    if q["type"] == "choice":
                        display = str(val)
                        for label, v in q["choices"]:
                            if v == val:
                                display = label
                                break
                        lines.append(f"| {q['label']} | {display} |")
                    else:
                        lines.append(f"| {q['label']} | {val} {q.get('unit', '')} |")

                summary = "\n".join(lines)
                prompt = ("### ✅ 全部问题已回答完毕\n\n以下是您确认的设计参数：\n\n"
                          + summary + "\n\n确认无误后点击下方按钮开始生成。")

                return (
                    gr.update(value=prompt, visible=True),     # bot_msg
                    gr.update(visible=False),                   # input_text hidden
                    gr.update(visible=False, choices=[]),       # input_choices hidden
                    gr.update(visible=False),                   # back_btn hidden
                    gr.update(visible=False),                   # next_btn hidden
                    gr.update(value=self.total_questions),     # progress_bar
                    gr.update(visible=True),                    # confirm_area
                    gr.update(value=summary),                  # confirm_summary
                    gr.update(visible=False),                   # result_area
                )

            def on_next(idx: int, answers: dict, text_val: Any, choice_val: Any):
                q = QUESTIONS[idx]
                answers = dict(answers)
                if q["type"] == "number":
                    try:
                        val = float(text_val) if text_val else q["default"]
                    except (ValueError, TypeError):
                        val = q["default"]
                    answers[q["id"]] = val
                else:
                    answers[q["id"]] = choice_val if choice_val is not None else q["default"]
                return _make_question_view(idx + 1, answers)

            def on_back(idx: int, answers: dict):
                return _make_question_view(max(0, idx - 1), answers)

            def on_confirm(answers: dict):
                """确认 - 一键生成全部."""
                params: dict[str, Any] = {}
                for q in QUESTIONS:
                    val = answers.get(q["id"], q["default"])
                    if q["id"] in ("wall_length", "wall_height", "column_spacing"):
                        params[q["id"]] = float(val) * 1000
                    else:
                        params[q["id"]] = val
                params.setdefault("panel_width", 600)
                params.setdefault("panel_height", 2400)
                params.setdefault("wind_pressure", None)

                try:
                    state = self.orchestrator.run_all("", params)
                except Exception as e:
                    return _error_view(str(e))

                return _make_results_view(state)

            def _make_results_view(state: DesignState):
                # 计算书
                report = ""
                if state.report_path:
                    try:
                        report = Path(state.report_path).read_text(encoding="utf-8")
                    except Exception:
                        report = "_计算书读取失败_"

                # 草图
                sketch = None
                if state.sketch_path:
                    try:
                        from PIL import Image
                        sketch = Image.open(state.sketch_path)
                    except Exception as exc:
                        logger.warning(f"草图加载失败: {exc}")

                # 效果图
                render = None
                if state.render_path:
                    try:
                        from PIL import Image
                        render = Image.open(state.render_path)
                    except Exception as exc:
                        logger.warning(f"效果图加载失败: {exc}")

                # STL
                stl_info = f"✅ STL 已导出\n📁 {state.stl_path}" if state.stl_path else "⚠️ STL 不可用 (需 CadQuery)"

                return (
                    gr.update(value="### 🎉 设计完成!", visible=True),    # bot_msg
                    gr.update(visible=False),                              # input_text
                    gr.update(visible=False, choices=[]),                  # input_choices
                    gr.update(visible=False),                              # back_btn
                    gr.update(visible=False),                              # next_btn
                    gr.update(value=self.total_questions),                 # progress_bar
                    gr.update(visible=False),                              # confirm_area
                    gr.update(value=""),                                   # confirm_summary
                    gr.update(visible=True),                               # result_area

                    # 结果区内容
                    "✅ 全部生成完毕",                                      # gen_status
                    report,                                                 # report_view
                    sketch,                                                 # sketch_view
                    render,                                                 # render_view
                    state.material_list,                                    # material_view
                    stl_info,                                               # stl_view
                )

            def _error_view(msg: str):
                return (
                    gr.update(value=f"### ❌ 生成失败\n\n{msg}", visible=True),
                    gr.update(visible=False), gr.update(visible=False, choices=[]),
                    gr.update(visible=False), gr.update(visible=False),
                    gr.update(value=0),
                    gr.update(visible=False), gr.update(value=""),
                    gr.update(visible=False),
                    f"❌ 失败: {msg}", "", None, None, None, "",
                )

            # ===== 事件绑定 (9 个通用输出) =====
            common_outputs = [bot_msg, input_text, input_choices, back_btn, next_btn,
                              progress_bar, confirm_area, confirm_summary, result_area]

            next_btn.click(
                fn=on_next,
                inputs=[q_index, answers_state, input_text, input_choices],
                outputs=common_outputs,
            )
            back_btn.click(
                fn=on_back,
                inputs=[q_index, answers_state],
                outputs=common_outputs,
            )
            edit_btn.click(
                fn=lambda answers: _make_question_view(0, answers),
                inputs=[answers_state],
                outputs=common_outputs,
            )

            confirm_btn.click(
                fn=on_confirm,
                inputs=[answers_state],
                outputs=common_outputs + [gen_status, report_view, sketch_view, render_view, material_view, stl_view],
            )

            # 初始渲染
            app.load(
                fn=lambda: _make_question_view(0, {}),
                outputs=common_outputs,
            )

        return app

    def launch(self, server_name: str = "0.0.0.0", server_port: int = 7860, share: bool = False):
        # [DEPRECATED_GUI] self.create_interface().launch(
            server_name=server_name, server_port=server_port, share=share, css=CSS,
        )


# [DEPRECATED_GUI] def create_interface(config: Config | None = None) -> gr.Blocks:
    return GradioApp(config).create_interface()