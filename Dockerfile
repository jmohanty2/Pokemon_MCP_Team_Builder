FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

WORKDIR /app

COPY pyproject.toml README.md server.py ./
COPY pokemon_mcp/ ./pokemon_mcp/
RUN pip install --no-cache-dir .

EXPOSE 8000

CMD ["python", "server.py"]
