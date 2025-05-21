from flask import Flask

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.sdk.resources import Resource as OTL_Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from kv_flask_hammer import config
from kv_flask_hammer.logger import get_logger


LOG = get_logger("traces")


# Set the service name that shows in traces

tracer: TracerProvider | None = None


def init_traces(flask_app: Flask) -> TracerProvider | None:
    global tracer

    if config.observ.traces_enabled:
        LOG.info("Initializing traces with endpoint: %s", config.observ.traces_endpoint_url)

        otl_resource = OTL_Resource(attributes={"service.name": config.observ.traces_service_name})
        tracer = TracerProvider(resource=otl_resource)
        trace.set_tracer_provider(tracer)
        otlp_span_exporter = OTLPSpanExporter(endpoint=config.observ.traces_endpoint_url)
        tracer.add_span_processor(BatchSpanProcessor(otlp_span_exporter))

        LoggingInstrumentor().instrument()
        FlaskInstrumentor().instrument_app(flask_app, tracer_provider=tracer)
        return tracer

    else:
        LOG.debug("Not initializing traces!")


__all__ = ["init_traces"]
