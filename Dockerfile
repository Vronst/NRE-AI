FROM python:3.12.10-slim as pyt

RUN pip install uv

# makes uv copy files instead of creating links
ENV UV_LINK_MODE=copy
# make .venv as primary python
ENV PATH="/app/.venv/bin:$PATH"

WORKDIR /app

# run first to avoid rebuilding if not necessary
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen

# not safe
# COPY .env .
COPY scripts/ ./scripts/
COPY src/ ./src/
COPY tests/ ./tests/
COPY README.md . 


RUN export UV_ENV_FILE="$(pwd)"

EXPOSE 8080
EXPOSE 8000
EXPOSE 9000

CMD ["uv", "run", "nre-ai"]
