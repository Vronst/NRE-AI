FROM python:3.12.10-slim as pyt

RUN pip install uv

# makes uv copy files instead of creating links
ENV UV_LINK_MODE=copy
# make .venv as primary python
ENV PATH="/app/.venv/bin:$PATH"
ENV CI=true
ENV CITY_PATH='/app/submodules/NRE/Assets/StreamingAssets/miasta.json'

WORKDIR /app

# run first to avoid rebuilding if not necessary
COPY pyproject.toml uv.lock README.md ./

COPY scripts/ ./scripts/
COPY src/ ./src/
COPY tests/ ./tests/
COPY submodules/ ./submodules/
COPY README.md . 
COPY docs/ ./docs/
COPY release-notes.txt ./release-notes.txt 
COPY release-title.txt ./release-title.txt

RUN uv sync --frozen

RUN export UV_ENV_FILE="$(pwd)"

EXPOSE 8080
EXPOSE 8000
EXPOSE 9000

# CMD ["uv", "run", "nre-ai"]
CMD ["sleep", "infinity"]
