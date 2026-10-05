import os
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field
from src.graph import run_incident_analysis
from src.schemas import RemediationPlan

app = FastAPI(
    title="Agentic DevOps Incident Copilot",
    description="Multi-Agent SRE Copilot using LangGraph, Qdrant Hybrid RAG, and Pydantic validation.",
    version="1.0.0"
)

class IncidentRequest(BaseModel):
    raw_logs: str = Field(
        ..., 
        description="Raw server logs, K8s events, or database exception traces.",
        json_schema_extra={"example": "2026-03-29T10:14:22Z pod/payment-service State: Terminated, ExitCode: 137, Reason: OOMKilled"}
    )

@app.get("/health", status_code=status.HTTP_200_OK)
def health_check():
    """Health check endpoint for Kubernetes liveness/readiness probes."""
    return {"status": "healthy", "service": "agentic-sre-copilot"}

@app.post(
    "/analyze-incident", 
    response_model=RemediationPlan, 
    status_code=status.HTTP_200_OK,
    summary="Analyze Raw Incident Logs",
    description="Runs raw logs through the Diagnostic Agent -> Qdrant Hybrid RAG -> Resolution Agent graph pipeline."
)
def analyze_incident(payload: IncidentRequest):
    if not payload.raw_logs.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="raw_logs field cannot be empty."
        )
    
    try:
        report = run_incident_analysis(payload.raw_logs)
        return report
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error executing agent pipeline: {str(e)}"
        )