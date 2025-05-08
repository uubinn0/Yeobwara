FROM python:3.13

WORKDIR /app

# 기본 툴 설치 + Node.js 설치 (npx 포함)
RUN apt-get update && apt-get install -y \
    curl build-essential git gnupg ca-certificates \
  && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
  && apt-get install -y nodejs \
  && curl -LsSf https://astral.sh/uv/install.sh | sh \
  && ln -s /root/.local/bin/uv /usr/local/bin/uv \
  && rm -rf /var/lib/apt/lists/*

# Dockerfile
RUN npm install -g @suekou/mcp-notion-server
RUN npm install -g @modelcontextprotocol/server-github
RUN npm install -g @modelcontextprotocol/server-gitlab


RUN uv pip install --system \
    fastapi \
    "uvicorn[standard]" \
    openai-agents

# 2) openai 버전을 1.15.x(≤1.15.0)로 강제 다운그레이드
RUN uv pip install --system --no-deps "openai==1.15.0"

# 앱 복사
COPY app/ ./app/

EXPOSE 8001

# 개발용 reload 포함 실행 명령
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
