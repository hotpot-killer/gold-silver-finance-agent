FROM python:3.12-slim

# 安装系统依赖 (playwright 需要这些依赖)
RUN apt-get update && apt-get install -y \
    libnss3 \
    libatk-bridge2.0-0 \
    libdrm2 \
    libxkbcommon-x11-0 \
    libxcb \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpci-dev \
    libcups2 \
    wget \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# 安装uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh -s && \
    /root/.cargo/bin/uv --version

# 设置工作目录
WORKDIR /app

# 复制项目文件
COPY pyproject.toml uv.lock ./
RUN /root/.cargo/bin/uv sync --frozen

# 安装 playwright 浏览器
RUN /root/.cargo/bin/uv run playwright install chromium

# 复制源代码
COPY . .

# 创建数据目录
RUN mkdir -p data cache

# 默认命令
CMD ["uv", "run", "python", "main.py", "--schedule"]
