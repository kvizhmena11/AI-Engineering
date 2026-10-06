# 🚀 Agentic DevOps Incident Copilot

> An enterprise-ready multi-agent SRE copilot built with **LangGraph**, **FastAPI**, **Qdrant**, and **Arize Phoenix**. Designed to automate incident diagnosis, execute runbook retrieval, and synthesize structured Kubernetes remediation plans.

---

## 📌 Project Overview & Technical Motivation

In modern cloud-native environments, incident response times (MTTR) are directly bound by human triage latency. SREs manually sift through noisy Kubernetes stack traces, map log errors to internal runbooks, and formulate remediation plans under severe time constraints.

This project was built to address that bottleneck by implementing an **autonomous, production-grade agentic pipeline** that converts unstructured incident logs into validated, deterministic remediation strategies.

Rather than relying on a naive single-prompt LLM wrapper, this system utilizes a **state-machine driven DAG architecture** with hard constraint enforcement, vector hybrid search, and full OpenTelemetry tracing—mirroring how modern AI Engineering platforms are built at scale.

---

## 🏗 System Architecture & Workflow




The incident pipeline operates as a directed acyclic graph (DAG):

1. **Diagnostic Node:** Parses unstructured raw logs, isolates the offending service/pod, identifies failure error codes (e.g., `OOMKilled`, `ExitCode: 137`), and assigns incident severity.
2. **Retrieval Node (Hybrid RAG):** Generates dense embeddings (`text-embedding-3-small`) to query a **Qdrant** vector database, extracting relevant internal runbooks and historical post-mortems.
3. **Resolution Node:** Synthesizes diagnosis and retrieved runbook contexts into actionable, step-by-step immediate fixes and long-term preventative measures.
4. **Validation Layer:** Enforces output schema compliance using **Pydantic v2** models before returning response to the caller.
5. **Observability Engine:** Streams full-execution OpenTelemetry spans (latency, prompt tokens, completion tokens) directly to **Arize Phoenix**.

---

## 🛠 Tech Stack

* **Language & Framework:** Python 3.11, FastAPI, Uvicorn
* **Agentic Orchestration:** LangGraph, LangChain Classic/Core
* **Vector Database:** Qdrant (Hybrid Vector & Payload Filtering)
* **Model Integration:** OpenAI (`gpt-4o-mini`, `text-embedding-3-small`)
* **Validation & Schemas:** Pydantic v2
* **Observability & Telemetry:** Arize Phoenix, OpenTelemetry (OTLP gRPC)
* **Testing & Quality Control:** Pytest, LLM-as-a-Judge Evaluation Suite
* **Containerization & Deployment:** Docker, Docker Compose

---

## 🚀 Key Features Built Across Phases

### 1. Hybrid RAG & Vector Storage
* Custom ingestion pipeline (`src/ingest.py`) parsing markdown runbooks into chunked vector payloads.
* Local and containerized Qdrant client integration with dynamic DNS resolution across local and containerized runtime environments.

### 2. Multi-Agent LangGraph State Machine
* Explicit state handling via `AgentState` typed dictionaries.
* Isolated reasoning phases prevent hallucination bleeding between log parsing and remediation generation.

### 3. Automated LLM-as-a-Judge Evaluation (`pytest`)
* Integrated automated evaluation suite assessing **Faithfulness** and **Context Relevance**.
* Programmatically verifies that generated remediation steps match grounding context retrieved from vector storage.

### 4. REST Microservice & OpenAPI Standardization
* Endpoints exposed via FastAPI (`/health` and `/analyze-incident`).
* Native input handling and error mapping for empty payloads (`400`), schema validation errors (`422`), and pipeline exceptions (`500`).

### 5. OpenTelemetry Observability (Arize Phoenix)
* End-to-end tracing enabled via `openinference-instrumentation-langchain`.
* Live tracking of token costs, execution node latency distribution, and raw prompt context debugging at `http://localhost:6006`.

### 6. Production Multi-Container Orchestration
* Fully containerized microservice stack configured via `docker-compose.yml`.
* Networked container communication linking `sre-copilot-api`, `sre-qdrant`, and `sre-phoenix`.

---

## ⚡ Quickstart & Local Setup

### Prerequisites
* Docker Desktop & Docker Compose
* Python 3.11+
* OpenAI API Key

### 1. Environment Setup
Clone the repository and create a `.env` file in the root directory:

```bash
git clone [https://github.com/your-username/agentic-sre.git](https://github.com/your-username/agentic-sre.git)
cd agentic-sre
echo "OPENAI_API_KEY=your_openai_api_key_here" > .env