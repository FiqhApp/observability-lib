import logging
from opentelemetry import trace, metrics, _logs
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter

__all__ = ["init_observability", "shutdown_otel"]


def init_observability(service_name: str, collector_endpoint: str = "http://otel-collector:4317"):
    resource = Resource.create({"service.name": service_name})

    # 1. TRACING: Setup Provider and Exporter
    tp = TracerProvider(resource=resource)
    tp.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=collector_endpoint, insecure=True)))
    trace.set_tracer_provider(tp)

    # 2. METRICS: Setup Provider and Reader
    mp = MeterProvider(resource=resource, metric_readers=[
        PeriodicExportingMetricReader(OTLPMetricExporter(endpoint=collector_endpoint, insecure=True))
    ])
    metrics.set_meter_provider(mp)

    # 3. LOGGING: Setup Provider and OTel Handler
    lp = LoggerProvider(resource=resource)
    lp.add_log_record_processor(BatchLogRecordProcessor(OTLPLogExporter(endpoint=collector_endpoint, insecure=True)))
    _logs.set_logger_provider(lp)

    # Attach OTel handler to standard python logging
    handler = LoggingHandler(logger_provider=lp)
    logging.getLogger().addHandler(handler)
    logging.getLogger().setLevel(logging.INFO)

    print(f"Observability initialized for {service_name} -> {collector_endpoint}")


# After calling init_observability...
def shutdown_otel(trace, metrics):
    trace.get_tracer_provider().shutdown()
    metrics.get_meter_provider().shutdown()
