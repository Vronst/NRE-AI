FROM python:3.12.10-slim AS pyt

RUN pip install uv

# makes uv copy files instead of creating links
ENV UV_LINK_MODE=copy
# make .venv as primary python
ENV PATH="/app/.venv/bin:$PATH"
ENV CI=true
ENV DATA_PATH='/app/submodules/NRE/Assets/Data/Save/'

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
RUN uv tool install ruff
RUN echo "alias lint1='uv tool run ruff check --fix'" >> /root/.bashrc \
    && echo "alias lint2='uv tool run ruff format'" >> /root/.bashrc

RUN export UV_ENV_FILE="$(pwd)"

EXPOSE 8080
EXPOSE 8000
EXPOSE 9000

# CMD ["uv", "run", "nre-ai"]
CMD ["sleep", "infinity"]
