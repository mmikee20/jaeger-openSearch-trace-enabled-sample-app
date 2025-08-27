FROM python:3.11-slim

WORKDIR /app
COPY app.py .

RUN pip install flask opentelemetry-api opentelemetry-sdk \
    opentelemetry-exporter-otlp opentelemetry-instrumentation-flask

CMD ["python", "app.py"]
