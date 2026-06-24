# ── Build stage ──────────────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /build

# Install system build dependencies required by WeasyPrint and other packages.
RUN apt-get update && apt-get install -y --no-install-recommends \
    # WeasyPrint runtime dependencies
    # libpango-1.0-0 \
    # libpangoft2-1.0-0 \
    # libpangocairo-1.0-0 \
    # libgdk-pixbuf-2.0-0 \
    # libffi-dev \
    # libcairo2 \
    # shared-mime-info \
    # Required for Pillow / image handling used by WeasyPrint
    # libjpeg-dev \
    # Compiler tools needed to build some Python packages
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


# ── Runtime stage ─────────────────────────────────────────────────────────────
FROM python:3.12-slim

WORKDIR /app

# Copy WeasyPrint system libraries from builder
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libffi8 \
    libcairo2 \
    libjpeg62-turbo \
    shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

# Copy installed Python packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application source
COPY app/ ./app/
COPY templates/ ./templates/
COPY alembic/ ./alembic/
COPY alembic.ini .

# Create a non-root user for security
RUN useradd --system --no-create-home appuser
USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
