import json
import pytest
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from src.graph import run_incident_analysis
from src.schemas import RemediationPlan

judge_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

class JudgeEvaluation(BaseModel):
    """Evaluation output schema from the LLM Judge."""
    faithfulness_score: float = Field(description="Score between 0.0 and 1.0 indicating if the plan is hallucination-free and faithful to logs/context.")
    context_relevance_score: float = Field(description="Score between 0.0 and 1.0 indicating how relevant the remediation steps are to the root cause.")
    reasoning: str = Field(description="Detailed explanation of the judge's scoring decision.")

def load_golden_dataset():
    with open("tests/golden_dataset.json", "r", encoding="utf-8") as f:
        return json.load(f)

@pytest.mark.parametrize("test_case", load_golden_dataset())
def test_agent_performance_and_eval(test_case):
    raw_logs = test_case["raw_logs"]
    
    # 1. Execute Agent Pipeline
    report: RemediationPlan = run_incident_analysis(raw_logs)

    # Assert 1: Schema Integrity Check (Pydantic structure validation)
    assert isinstance(report, RemediationPlan)
    assert len(report.immediate_fixes) > 0
    assert len(report.preventative_actions) > 0
    assert 0.0 <= report.confidence_score <= 1.0

    # Assert 2: Keyword Ground Truth Check (Deterministic)
    report_text = f"{report.root_cause} {' '.join(report.immediate_fixes)}".lower()
    matched_terms = [term for term in test_case["key_root_cause_terms"] if term.lower() in report_text]
    assert len(matched_terms) >= 1, f"Report missed core concepts for {test_case['test_id']}. Expected terms: {test_case['key_root_cause_terms']}"

    # Assert 3: LLM-as-a-Judge Evaluation (Non-Deterministic / Semantic Quality)
    structured_judge = judge_llm.with_structured_output(JudgeEvaluation)
    judge_prompt = f"""
    You are an expert Principal SRE Evaluation Judge. Evaluate the quality of an automated SRE Incident Remediation Report.

    RAW INCIDENT LOGS:
    {raw_logs}

    GENERATED REMEDIATION REPORT:
    - Service: {report.service_name}
    - Severity: {report.severity}
    - Root Cause: {report.root_cause}
    - Immediate Fixes: {report.immediate_fixes}
    - Preventative Actions: {report.preventative_actions}

    Grade the report on:
    1. Faithfulness: Is the root cause accurate to the logs without hallucinating unrelated system failures?
    2. Context Relevance: Are the proposed immediate fixes actionable and standard industry solutions?

    Provide scores between 0.0 and 1.0.
    """
    
    eval_result: JudgeEvaluation = structured_judge.invoke(judge_prompt)

    print(f"\n--- EVALUATION METRICS [{test_case['test_id']}] ---")
    print(f"Faithfulness Score: {eval_result.faithfulness_score}")
    print(f"Context Relevance Score: {eval_result.context_relevance_score}")
    print(f"Judge Reasoning: {eval_result.reasoning}\n")

    assert eval_result.faithfulness_score >= 0.7, f"Faithfulness score too low: {eval_result.faithfulness_score}"
    assert eval_result.context_relevance_score >= 0.7, f"Relevance score too low: {eval_result.context_relevance_score}"