import os
from typing import Dict, Any
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from qdrant_client import QdrantClient
from langgraph.graph import StateGraph, END

from src.schemas import AgentState, LogSignature, RemediationPlan

load_dotenv()

QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", 6333))
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "sre_runbooks")

# Initialize LLM & Embeddings
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
qdrant_client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

# --- Node 1: Diagnostic Agent ---
def diagnostic_node(state: AgentState) -> Dict[str, Any]:
    structured_llm = llm.with_structured_output(LogSignature)
    prompt = f"""
    You are an expert SRE Diagnostic Agent. Analyze the following raw server logs and extract core failure metadata:
    
    LOGS:
    {state.raw_logs}
    """
    result = structured_llm.invoke(prompt)
    return {"log_signature": result}

# --- Node 2: Retrieval Node ---
def retrieval_node(state: AgentState) -> Dict[str, Any]:
    signature = state.log_signature
    if not signature:
        return {"retrieved_docs": []}

    # Dense Vector Search using updated Qdrant API
    query_vector = embeddings.embed_query(signature.query_string)
    search_response = qdrant_client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        limit=3
    )

    docs = [hit.payload["page_content"] for hit in search_response.points if "page_content" in hit.payload]
    return {"retrieved_docs": docs}

# --- Node 3: Resolution Agent ---
def resolution_node(state: AgentState) -> Dict[str, Any]:
    signature = state.log_signature
    context = "\n---\n".join(state.retrieved_docs) if state.retrieved_docs else "No runbooks found."

    structured_llm = llm.with_structured_output(RemediationPlan)
    prompt = f"""
    You are an On-Call Senior SRE Copilot. Generate a structured remediation report for this incident.
    
    SERVICE: {signature.service_name if signature else 'Unknown'}
    SEVERITY: {signature.severity if signature else 'UNKNOWN'}
    FAILURE SIGNATURE: {signature.error_signature if signature else 'N/A'}
    
    RETRIEVED RUNBOOK CONTEXT:
    {context}
    
    ORIGINAL LOGS:
    {state.raw_logs}
    """
    report = structured_llm.invoke(prompt)
    return {"final_report": report}

# --- Build LangGraph Pipeline ---
workflow = StateGraph(AgentState)

workflow.add_node("diagnostic", diagnostic_node)
workflow.add_node("retrieval", retrieval_node)
workflow.add_node("resolution", resolution_node)

workflow.set_entry_point("diagnostic")
workflow.add_edge("diagnostic", "retrieval")
workflow.add_edge("retrieval", "resolution")
workflow.add_edge("resolution", END)

app = workflow.compile()

# Execution Helper
def run_incident_analysis(raw_logs: str) -> RemediationPlan:
    initial_state = AgentState(raw_logs=raw_logs)
    output = app.invoke(initial_state)
    return output["final_report"]

if __name__ == "__main__":
    sample_log = """
    2026-03-29T10:14:22Z pod/payment-service-7f89d98b6-x4k21 container/payment-app 
    Kernel log: Memory cgroup out of memory: Kill process 18291 (python) score 950 or sacrifice child
    State: Terminated, ExitCode: 137, Reason: OOMKilled
    """
    print("Testing multi-agent graph pipeline...")
    report = run_incident_analysis(sample_log)
    print("\n--- INCIDENT REMEDIATION REPORT ---")
    print(report.model_dump_json(indent=2))