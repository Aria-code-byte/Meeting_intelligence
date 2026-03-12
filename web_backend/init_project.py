#!/usr/bin/env python3
"""
Jinni 会议精灵 - 项目初始化脚本
==============================
一键创建必要的目录结构和数据库

使用方式：
    python init_project.py
"""

import os
import sys
from pathlib import Path


def create_directory_structure():
    """创建项目目录结构"""
    print("📁 创建目录结构...")

    # 定义目录列表
    directories = [
        "storage",           # 存储根目录
        "storage/videos",    # 上传的视频文件
        "storage/db",        # SQLite 数据库
        "storage/transcripts",  # 转录结果
        "storage/cache",     # 缓存文件
        "core",              # C++ 引擎目录
        "logs",              # 日志文件
    ]

    base_dir = Path(__file__).parent

    for dir_path in directories:
        full_path = base_dir / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"  ✓ {dir_path}/")

    # 创建 .gitkeep 保持空目录在 git 中
    for dir_path in directories:
        (base_dir / dir_path / ".gitkeep").touch(exist_ok=True)

    print("✅ 目录结构创建完成\n")


def initialize_database():
    """初始化 SQLite 数据库"""
    print("🗄️  初始化数据库...")

    try:
        from models import Base
        from sqlalchemy import create_engine, inspect

        # 获取数据库路径
        base_dir = Path(__file__).parent
        db_dir = base_dir / "storage" / "db"
        db_dir.mkdir(parents=True, exist_ok=True)
        db_path = db_dir / "jinni.db"

        # 创建数据库引擎
        database_url = f"sqlite:///{db_path}"
        engine = create_engine(
            database_url,
            connect_args={"check_same_thread": False},
        )

        # 创建所有表
        Base.metadata.create_all(bind=engine)

        # 检查创建的表
        inspector = inspect(engine)
        tables = inspector.get_table_names()

        for table in tables:
            print(f"  ✓ 表: {table}")

        print(f"  📁 数据库文件: {db_path}")
        print("✅ 数据库初始化完成\n")

    except ImportError as e:
        print(f"❌ 导入错误: {e}")
        print("请确保已安装依赖: pip install sqlalchemy")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 数据库初始化失败: {e}")
        sys.exit(1)


def create_cpp_engine_stub():
    """创建 C++ 引擎存根文件（用于测试）"""
    print("🔧 创建 C++ 引擎存根...")

    core_dir = Path(__file__).parent / "core"
    engine_path = core_dir / "jinni_engine"

    # 创建 README 说明如何编译 C++ 引擎
    readme_path = core_dir / "README.md"
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write("""# Jinni 核心引擎 (C++)

## 编译说明

### 依赖
- C++17 或更高版本
- FFmpeg 库 (libavformat, libavcodec)
- nlohmann/json
- libcurl (用于 API 调用)

### 编译命令
```bash
g++ -std=c++17 -O3 \\
    -I/usr/include/ffmpeg \\
    -lavformat -lavcodec -lavutil -lswresample \\
    -lcurl \\
    jinni_engine.cpp \\
    -o jinni_engine
```

### 测试运行
```bash
./jinni_engine --help
```

## Python 调用方式

后端通过 subprocess 调用：
```bash
./jinni_engine --input video.mp4 --output result.json --llm deepseek
```
""")

    print(f"  ✓ {readme_path}")

    # 创建 Python 版本的模拟引擎（用于开发测试）
    stub_path = core_dir / "jinni_engine.py"
    with open(stub_path, "w", encoding="utf-8") as f:
        f.write("""#!/usr/bin/env python3
\"\"\"
Jinni 引擎 Python 模拟版（用于开发测试）
实际生产环境使用 C++ 编译版本
\"\"\"

import argparse
import json
import time
import uuid
from pathlib import Path


def mock_process_video(input_path: str, output_path: str, llm: str = "deepseek"):
    \"\"\"模拟视频处理\"\"\"
    print(f"🎬 处理视频: {input_path}")

    # 模拟处理时间
    time.sleep(2)

    # 模拟结果
    result = {
        "transcript_raw": "这是原始转录文本...\\n\\n示例内容：",
        "transcript_enhanced": "这是经过 DeepSeek LLM 增强后的转录文本...\\n\\n修正了错别字，优化了语句结构。",
        "summaries": [
            {
                "role": "产品经理",
                "content": {
                    "sections": [
                        {"title": "会议议题", "content": "讨论了产品迭代计划"},
                        {"title": "决策事项", "content": "确定下个版本优先级"},
                    ]
                },
            },
            {
                "role": "开发者",
                "content": {
                    "sections": [
                        {"title": "技术方案", "content": "采用微服务架构"},
                        {"title": "实施计划", "content": "预计 2 周完成"},
                    ]
                },
            },
        ],
        "metadata": {
            "duration": 1800.5,
            "word_count": 5000,
            "processing_time": 45.2,
            "llm_provider": llm,
            "llm_model": "deepseek-chat",
        }
    }

    # 保存结果
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"✅ 结果已保存: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Jinni 会议处理引擎")
    parser.add_argument("--input", required=True, help="输入视频路径")
    parser.add_argument("--output", required=True, help="输出 JSON 路径")
    parser.add_argument("--llm", default="deepseek", help="LLM 提供商")
    args = parser.parse_args()

    mock_process_video(args.input, args.output, args.llm)


if __name__ == "__main__":
    main()
""")

    # 使 Python 模拟引擎可执行
    stub_path.chmod(0o755)
    print(f"  ✓ {stub_path} (Python 模拟版)")

    print("✅ C++ 引擎存根创建完成\n")
    print("💡 提示：生产环境请编译真正的 C++ 引擎替换 Python 模拟版")


def create_env_template():
    """创建环境变量模板"""
    print("📝 创建环境变量模板...")

    env_path = Path(__file__).parent / ".env.example"
    with open(env_path, "w", encoding="utf-8") as f:
        f.write("""# Jinni 会议精灵 - 环境变量配置

# DeepSeek API 配置
DEEPSEEK_API_KEY=sk-xxxxx

# 备用 LLM（可选）
OPENAI_API_KEY=sk-xxxxx
ANTHROPIC_API_KEY=sk-xxxxx

# 服务配置
API_HOST=0.0.0.0
API_PORT=8000
STREAMLIT_PORT=8501

# 数据库配置
DATABASE_URL=sqlite:///storage/db/jinni.db

# 文件上传限制
MAX_UPLOAD_SIZE_MB=500
""")

    print(f"  ✓ {env_path}")
    print("✅ 环境变量模板创建完成\n")


def create_gitignore():
    """创建 .gitignore"""
    print("📝 创建 .gitignore...")

    gitignore_path = Path(__file__).parent / ".gitignore"
    content = """# Jinni 会议精灵 - Git 忽略文件

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
*.egg-info/
dist/
build/

# 虚拟环境
.venv/
venv/
env/

# IDE
.vscode/
.idea/
*.swp
*.swo

# 存储文件（保留目录结构）
storage/videos/*
storage/db/*
storage/transcripts/*
storage/cache/*
!storage/*/.gitkeep

# 日志
logs/*.log

# 环境变量（包含敏感信息）
.env

# C++ 编译产物
core/jinni_engine
core/*.o
core/*.so

# 操作系统
.DS_Store
Thumbs.db
"""

    with open(gitignore_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"  ✓ {gitignore_path}")
    print("✅ .gitignore 创建完成\n")


def main():
    """主函数"""
    print("""
    ╔════════════════════════════════════════════════════════════╗
    ║           🧞 Jinni 会议精灵 - 项目初始化                    ║
    ╠════════════════════════════════════════════════════════════╣
    ║  正在创建项目结构和配置文件...                              ║
    ╚════════════════════════════════════════════════════════════╝
    """)

    try:
        create_directory_structure()
        initialize_database()
        create_cpp_engine_stub()
        create_env_template()
        create_gitignore()

        print("=" * 60)
        print("✅ 项目初始化完成！")
        print("=" * 60)
        print()
        print("📋 下一步操作：")
        print("  1. 安装依赖：pip install -r requirements.txt")
        print("  2. 配置环境：cp .env.example .env 并编辑 API Key")
        print("  3. 启动后端：python main.py")
        print("  4. 启动前端：streamlit run app.py")
        print()
        print("💡 提示：开发环境可使用 Python 模拟引擎测试")
        print("   生产环境请编译真正的 C++ 引擎")
        print()

    except KeyboardInterrupt:
        print("\\n❌ 用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\\n❌ 初始化失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
