#!/bin/bash
# MoneyPrinterTurbo 部署检查脚本
# 用法: bash references/deploy-check.sh

set -e

PROJECT_DIR="$HOME/openclaw-workspace/MoneyPrinterTurbo"

echo "=== MoneyPrinterTurbo 部署检查 ==="
echo ""

# 1. 检查目录
if [ ! -d "$PROJECT_DIR" ]; then
  echo "❌ 未找到项目目录: $PROJECT_DIR"
  echo "请先运行: git clone https://github.com/harry0703/MoneyPrinterTurbo.git"
  exit 1
fi
echo "✅ 项目目录存在: $PROJECT_DIR"

cd "$PROJECT_DIR"

# 2. 检查 Python 版本
PY_VERSION=$(python3 --version 2>/dev/null | grep -oP '\d+\.\d+' | head -1)
echo "✅ Python 版本: $(python3 --version 2>&1)"

# 3. 检查 uv
if command -v uv &>/dev/null; then
  echo "✅ uv 已安装: $(uv --version)"
else
  echo "⚠️  uv 未安装，建议安装: https://docs.astral.sh/uv/"
fi

# 4. 检查依赖
if [ -d ".venv" ]; then
  echo "✅ 虚拟环境存在"
elif [ -f "uv.lock" ]; then
  echo "⚠️  uv.lock 存在但 .venv 未创建，运行: uv sync --frozen"
else
  echo "⚠️  未安装依赖，运行: uv sync --frozen"
fi

# 5. 检查配置文件
if [ -f "config.toml" ]; then
  echo "✅ config.toml 存在"
  # 检查是否配置了 API Key
  if grep -q 'api_key = ""' config.toml; then
    echo "⚠️  config.toml 中仍有未填写的 api_key，请编辑配置"
  else
    echo "✅ API Key 已配置"
  fi
else
  echo "⚠️  config.toml 不存在，运行: cp config.example.toml config.toml"
fi

# 6. 检查 ffmpeg
if command -v ffmpeg &>/dev/null; then
  echo "✅ ffmpeg 已安装: $(ffmpeg -version 2>&1 | head -1)"
else
  echo "⚠️  ffmpeg 未安装，MoviePy 会尝试自动下载"
fi

# 7. 检查端口占用
for PORT in 8501 8080; do
  if lsof -i :$PORT &>/dev/null; then
    echo "⚠️  端口 $PORT 已被占用"
  else
    echo "✅ 端口 $PORT 可用"
  fi
done

echo ""
echo "=== 检查完成 ==="
echo ""
echo "启动 WebUI: cd $PROJECT_DIR && uv run streamlit run ./webui/Main.py"
echo "启动 API:   cd $PROJECT_DIR && uv run python main.py"
