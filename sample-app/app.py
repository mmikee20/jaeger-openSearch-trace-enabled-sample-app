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
