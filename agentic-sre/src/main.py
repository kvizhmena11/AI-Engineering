import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

# OpenTelemetry & Arize Phoenix Instrumentation
from openinference.instrumentation.langchain import LangChainInstrumentor
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# Setup OpenTelemetry tracer pointing to the Arize Phoenix collector
phoenix_grpc_url = os.getenv("PHOENIX_COLLECTOR_ENDPOINT", "http://phoenix:4317")
tracer_provider = TracerProvider()
tracer_provider.add_span_processor(
    BatchSpanProcessor(OTLPSpanExporter(endpoint=phoenix_grpc_url, insecure=True))
)
trace.set_tracer_provider(tracer_provider)

# Instrument LangChain & LangGraph to automatically trace all agent invocations
LangChainInstrumentor().instrument(tracer_provider=tracer_provider)

# Import graph execution entrypoint
from src.graph import run_incident_analysis, RemediationPlan

app = FastAPI(
    title="Agentic DevOps Incident Copilot",
    description="Multi-Agent SRE Copilot using LangGraph, Qdrant Hybrid RAG, and Pydantic validation.",
    version="1.0.0",
)


class IncidentRequest(BaseModel):
    raw_logs: str = Field(
        ...,
        description="Raw log text or stack trace from Kubernetes / application monitor",
        example="2026-03-29T10:14:22Z pod/payment-service State: Terminated, ExitCode: 137, Reason: OOMKilled",
    )


@app.get("/health", tags=["Health"])
def health_check():
    """Health check endpoint for Kubernetes liveness/readiness probes."""
    return {"status": "ok", "service": "agentic-sre-copilot"}


@app.post(
    "/analyze-incident",
    response_model=RemediationPlan,
    tags=["Incident Analysis"],
    summary="Analyze Raw Incident Logs",
    description="Runs raw logs through the Diagnostic Agent -> Qdrant Hybrid RAG -> Resolution Agent graph pipeline.",
)
def analyze_incident(request: IncidentRequest):
    if not request.raw_logs.strip():
        raise HTTPException(status_code=400, detail="raw_logs field cannot be empty.")

    try:
        result = run_incident_analysis(request.raw_logs)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error executing agent pipeline: {str(e)}"
        )