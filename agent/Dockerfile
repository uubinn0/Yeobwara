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

# “글로벌 패키지”로 Node 모듈을 설치
RUN npm install -g @suekou/mcp-notion-server
RUN npm install -g @zereight/mcp-gitlab
RUN npm install -g @winterjung/mcp-korean-spell
RUN npm install -g duckduckgo-mcp-server
RUN npm install -g @modelcontextprotocol/server-sequential-thinking
RUN npm install -g @modelcontextprotocol/server-github
RUN npm install -g @openbnb/mcp-server-airbnb
RUN npm install -g figma-developer-mcp

### python 기반
# 논문 검색 서버 소스 클론 후 설치
RUN git clone https://github.com/openags/paper-search-mcp.git /srv/paper-search-mcp
WORKDIR /srv/paper-search-mcp
RUN pip install --no-cache-dir .
# dart 서버 소스 클론 후 설치
RUN git clone https://github.com/2geonhyup/dart-mcp.git /srv/dart-mcp
WORKDIR /srv/dart-mcp
RUN pip install --no-cache-dir .

### npm 로컬 
# 카카오 지도 서버 소스 클론 후 설치
RUN git clone https://github.com/cgoinglove/mcp-server-kakao-map.git /srv/mcp-server-kakao-map
WORKDIR /srv/mcp-server-kakao-map
RUN npm install
RUN npm run build

# poke mcp
RUN git clone https://github.com/NaveenBandarage/poke-mcp.git /srv/poke-mcp
WORKDIR /srv/poke-mcp
RUN npm install
RUN npm install -D ts-node typescript
RUN npm install -g ts-node typescript
RUN npm run build


# Python 패키지 설치
WORKDIR /app
RUN uv pip install --system \
    fastapi uvicorn[standard] openai-agents openai


# 앱 복사
COPY app/ ./app/

EXPOSE 8001

# 개발용 reload 포함 실행 명령
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
