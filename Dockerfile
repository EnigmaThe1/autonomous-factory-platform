FROM python:3.13-slim

WORKDIR /app

# Install dependencies
COPY pyproject.toml .
RUN pip install --no-cache-dir ".[postgres]"

# Copy source
COPY src/ src/
COPY dashboard/ dashboard/
COPY alembic/ alembic/
COPY alembic.ini .

# Install the package
RUN pip install --no-cache-dir -e .

EXPOSE 8000

CMD ["uvicorn", "af_core.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
