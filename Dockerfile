# Ships the recall_engine HTTP server with every extra installed.
# Must not bake in a dataset: users mount their own JSON file at /data.
FROM ghcr.io/astral-sh/uv:python3.12-trixie-slim

RUN groupadd --system --gid 999 recall \
 && useradd --system --gid 999 --uid 999 --create-home recall

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

# Dependencies first so source edits do not invalidate the heavy layer.
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project --extra all

COPY . /app
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --extra all

ENV PATH="/app/.venv/bin:$PATH"

USER recall

EXPOSE 8000

ENTRYPOINT ["recall_engine"]
CMD ["serve", "--host", "0.0.0.0", "--port", "8000", "--dataset", "/data/docs.json", "--data-key", "docs"]
