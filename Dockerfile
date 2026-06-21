# ============================================================
# Stage 1 — builder
#   安装 Python 依赖，并预下载 BAAI/bge-small-zh-v1.5 Embedding
#   模型到镜像内（≈130MB），避免容器首次启动时联网下载。
# ============================================================
FROM python:3.11-slim AS builder

WORKDIR /build

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    # 控制 HuggingFace 缓存落在 builder 内的 /hf_cache
    HF_HOME=/hf_cache

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# 预下载 Embedding 模型（构建时需联网；离线环境可删除此步骤，
# 并在 docker-compose.yml 中挂载 HF 缓存 volume）
RUN python -c "\
from langchain_huggingface import HuggingFaceEmbeddings; \
HuggingFaceEmbeddings(model_name='BAAI/bge-small-zh-v1.5', \
    model_kwargs={'device': 'cpu'}); \
print('Embedding model cached.')"


# ============================================================
# Stage 2 — runtime
#   精简镜像：只含运行时所需的包和模型，不含 pip、build 工具
# ============================================================
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    # 让 pip --user 安装的包和命令可被找到
    PATH="/root/.local/bin:$PATH" \
    # 指向 builder 阶段预下载的模型目录
    HF_HOME=/app/.cache/huggingface

# curl 仅用于 HEALTHCHECK；装完立即清理 apt 缓存
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# 从 builder 复制已安装的 Python 包
COPY --from=builder /root/.local /root/.local

# 从 builder 复制预下载的 HuggingFace 模型
COPY --from=builder /hf_cache /app/.cache/huggingface

WORKDIR /app

# 最后才复制应用代码，使前面的 layer 充分复用缓存
COPY app/ ./app/

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
