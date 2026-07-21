"""AKO_Wall_Designer_Agent 主入口 - 围墙设计智能体."""

import argparse
import sys
from pathlib import Path

# 将项目根目录添加到 Python 路径
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.agents.orchestrator import WallDesignerOrchestrator
from src.utils.config import Config
from src.utils.logging import get_logger, setup_logging


def run_cli(config: Config) -> None:
    """以 CLI 模式运行 - 命令行交互.

    Args:
        config: 应用配置
    """
    logger = get_logger("cli")
    logger.info("启动 CLI 模式")

    print("\n" + "=" * 60)
    print("🏗️  AKO_Wall_Designer_Agent - CLI 模式")
    print("=" * 60)
    print("输入 'quit' 退出, 'help' 查看帮助\n")

    orchestrator = WallDesignerOrchestrator(config=config)

    while True:
        try:
            user_input = input("📝 描述您的围墙设计需求: ").strip()

            if user_input.lower() in ("quit", "exit", "q"):
                print("👋 再见!")
                break

            if user_input.lower() == "help":
                print("\n示例输入:")
                print("  - 设计一段50米长的清水混凝土围墙，高度2.4米，柱间距3.6米")
                print("  - 100米钢柱围墙，高3米，柱距4.2米，深圳地区\n")
                continue

            if not user_input:
                continue

            print("\n🔄 正在处理...\n")

            result = orchestrator.run_sync(user_input)

            status = result.get("status", "未知")
            print(f"\n✅ 状态: {status}")
            print(f"📄 计算书: {result.get('report_path', 'N/A')}")
            print(f"📐 草图: {result.get('sketch_path', 'N/A')}")
            print(f"🎨 效果图: {result.get('render_path', 'N/A')}")
            print(f"📦 3D模型: {result.get('model_path', 'N/A')}")

            if result.get("error_message"):
                print(f"⚠️  错误: {result['error_message']}")

            # 打印材料清单
            material_list = result.get("material_list")
            if material_list:
                print("\n📦 材料清单:")
                panels = material_list.get("panels", {})
                columns = material_list.get("columns", {})
                print(f"  墙板: {panels.get('total', 0)} 块")
                print(f"  柱: {columns.get('count', 0)} 根 ({columns.get('material', 'N/A')})")

            print("\n" + "-" * 40)

        except KeyboardInterrupt:
            print("\n👋 已中断")
            break
        except Exception as e:
            print(f"\n❌ 处理失败: {e}")


def run_gradio(config: Config) -> None:
    """以 Gradio Web 模式运行.

    Args:
        config: 应用配置
    """
    logger = get_logger("gradio")
    logger.info("启动 Gradio Web 模式")

    from src.ui.gradio_app import GradioApp

    app = GradioApp(config)
    app.launch(
        server_name=config.host,
        server_port=config.port,
    )


def main() -> None:
    """主函数 - 解析命令行参数并启动对应模式."""
    parser = argparse.ArgumentParser(
        description="AKO_Wall_Designer_Agent - 装配式围墙设计智能体",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python src/main.py                    # 启动 Gradio Web 界面
  python src/main.py --cli              # 启动 CLI 模式
  python src/main.py --port 8080        # 指定端口
        """,
    )

    parser.add_argument(
        "--cli",
        action="store_true",
        help="使用 CLI 命令行模式",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="Web 服务器端口 (默认: 7860)",
    )
    parser.add_argument(
        "--host",
        type=str,
        default=None,
        help="Web 服务器地址 (默认: 0.0.0.0)",
    )
    parser.add_argument(
        "--no-llm",
        action="store_true",
        help="禁用 LLM, 仅使用规则解析",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default=None,
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="日志级别",
    )

    args = parser.parse_args()

    # 初始化配置
    config = Config.from_env()

    if args.port:
        config.port = args.port
    if args.host:
        config.host = args.host
    if args.log_level:
        config.log_level = args.log_level

    # 配置日志
    setup_logging(level=config.log_level)

    # 确保输出目录存在
    config.ensure_output_dirs()

    # 启动模式
    if args.cli:
        run_cli(config)
    else:
        run_gradio(config)


if __name__ == "__main__":
    main()