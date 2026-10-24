# One image definition for every service container.
# Build a specific service with:  docker build --build-arg SERVICE=telemetry_service -t ozagrimate-telemetry .
FROM python:3.12-slim

ARG SERVICE
ARG PORT=8000
ENV SERVICE=${SERVICE} PORT=${PORT} PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Only shared code and the selected service are copied in, so a service cannot depend on another one (ADR 01, ADR 07).
COPY services/__init__.py services/__init__.py
COPY services/shared services/shared
COPY services/${SERVICE} services/${SERVICE}

EXPOSE ${PORT}
CMD ["sh", "-c", "uvicorn services.${SERVICE}.main:app --host 0.0.0.0 --port ${PORT}"]
