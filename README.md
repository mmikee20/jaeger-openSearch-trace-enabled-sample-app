Jaeger + OpenSearch + Trace-Enabled Sample App
===================================================

Description
================
This exercise helps you set up distributed tracing with:
  OpenSearch (as the trace store),
  Jaeger Collector and Query UI (as the tracing system),
  A sample Python Flask app instrumented with OpenTelemetry (emits spans via OTLP HTTP).

Directory Structure
=========================
jaeger-tracing/
├── docker-compose.yml
├── sample-app/
│   ├── Dockerfile
│   └── app.py

docker-compose.yml
===============================
version: '3.8'

services:
  opensearch:
    image: opensearchproject/opensearch:2
    container_name: opensearch
    environment:
      - discovery.type=single-node
      - plugins.security.disabled=true
      - OPENSEARCH_JAVA_OPTS=-Xms512m -Xmx512m
    ulimits:
      memlock:
        soft: -1
        hard: -1
    ports:
      - "9200:9200"
    volumes:
      - ./opensearch-data:/usr/share/opensearch/data
    networks:
      - tracing-net

  jaeger-collector:
    image: jaegertracing/jaeger-collector:latest
    container_name: jaeger-collector
    environment:
      - SPAN_STORAGE_TYPE=elasticsearch
      - ES_SERVER_URLS=http://opensearch:9200
    ports:
      - "4317:4317"  # OTLP gRPC
      - "4318:4318"  # OTLP HTTP
    depends_on:
      - opensearch
    networks:
      - tracing-net

  jaeger-query:
    image: jaegertracing/jaeger-query:latest
    container_name: jaeger-query
    environment:
      - SPAN_STORAGE_TYPE=elasticsearch
      - ES_SERVER_URLS=http://opensearch:9200
    ports:
      - "16686:16686"
    depends_on:
      - opensearch
    networks:
      - tracing-net

  sample-app:
    build: ./sample-app
    container_name: sample-app
    environment:
      - OTEL_EXPORTER_OTLP_ENDPOINT=http://jaeger-collector:4318
      - OTEL_SERVICE_NAME=sample-app
    ports:
      - "5000:5000"
    depends_on:
      - jaeger-collector
    networks:
      - tracing-net

networks:
  tracing-net:
    driver: bridge


sample-app/Dockerfile
=============================
FROM python:3.11-slim

WORKDIR /app
COPY app.py .

RUN pip install flask opentelemetry-api opentelemetry-sdk \
    opentelemetry-exporter-otlp opentelemetry-instrumentation-flask

CMD ["python", "app.py"]


sample-app/app.py
============================
from flask import Flask
from opentelemetry import trace
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# Set up tracing
trace.set_tracer_provider(TracerProvider())
otlp_exporter = OTLPSpanExporter(endpoint="http://jaeger-collector:4318/v1/traces")
trace.get_tracer_provider().add_span_processor(BatchSpanProcessor(otlp_exporter))

app = Flask(__name__)
FlaskInstrumentor().instrument_app(app)
tracer = trace.get_tracer(__name__)

@app.route("/")
def index():
    with tracer.start_as_current_span("index-span"):
        return "Hello from traced app!"

@app.route("/slow")
def slow():
    import time
    with tracer.start_as_current_span("slow-span"):
        time.sleep(2)
        return "This was a slow response."

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

How to Run
===========================
From the root of your project (jaeger-tracing/):
docker-compose up --build


Access Points
==========================
Jaeger UI: http://localhost:16686

Sample App: http://localhost:5000

Sample Endpoint with Delay: http://localhost:5000/slow


Verify
==========================
Access the app via / and /slow.

Open Jaeger UI.

Select the sample-app service.

View traces and spans, including duration and endpoint paths.
