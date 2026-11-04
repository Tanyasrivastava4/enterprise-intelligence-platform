import time
import json
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from app.services.retrieval.hybrid_search import hybrid_retriever
from app.services.llm.fallback_router import llm_router

# ==============================================================================
# Tool 1: Knowledge Base Search
# ==============================================================================
class KBSearchInput(BaseModel):
    query: str = Field(description="Search query to locate relevant technical documents or logs.")
    top_k: int = Field(default=5, description="Number of document chunks to retrieve.")
    document_name_filter: Optional[str] = Field(default=None, description="Optional document name filter.")

def execute_kb_search(query: str, top_k: int = 5, document_name_filter: Optional[str] = None) -> Dict[str, Any]:
    """Retrieves grounded document chunks using hybrid (dense vector + BM25) search."""
    chunks = hybrid_retriever.search(query=query, top_k=top_k)
    
    if document_name_filter:
        chunks = [c for c in chunks if document_name_filter.lower() in c.get("document_name", "").lower()]

    formatted_results = []
    for c in chunks:
        formatted_results.append({
            "chunk_id": c.get("chunk_id"),
            "document_name": c.get("document_name"),
            "page_or_row": c.get("page_or_row", 1),
            "text": c.get("text", "")
        })

    return {
        "found_count": len(formatted_results),
        "results": formatted_results
    }


# ==============================================================================
# Tool 2: Document Analysis & Pattern Extraction
# ==============================================================================
class DocAnalysisInput(BaseModel):
    target_content: str = Field(description="The textual content or search results to deeply analyze.")
    analysis_focus: str = Field(description="Specific analytical focus, e.g., 'root_cause', 'anomalies', 'comparative_analysis'.")

async def execute_doc_analysis(target_content: str, analysis_focus: str) -> Dict[str, Any]:
    """Performs deep analytical synthesis on provided document content."""
    prompt = (
        f"You are an expert Enterprise Systems Analyst.\n"
        f"Perform an in-depth analysis of the following technical content with focus on: '{analysis_focus}'.\n\n"
        f"Content to analyze:\n{target_content[:3000]}\n\n"
        f"Structure your response with:\n"
        f"1. Identified Recurring Patterns / Themes\n"
        f"2. Core Technical Findings & Root Causes\n"
        f"3. Operational Gaps or Risk Areas"
    )

    llm_res = await llm_router.generate_with_fallback(
        prompt=prompt,
        system_prompt="You analyze enterprise technical documentation with rigorous engineering standards.",
        temperature=0.2,
        max_tokens=900
    )

    return {
        "analysis_focus": analysis_focus,
        "synthesis": llm_res.content,
        "model_used": llm_res.model
    }


# ==============================================================================
# Tool 3: Structured Report Generation
# ==============================================================================
class ReportGenInput(BaseModel):
    title: str = Field(description="Title of the structured report.")
    executive_summary: str = Field(description="Executive summary of the situation or investigation.")
    key_findings: List[str] = Field(description="List of verified technical findings with evidence.")
    recommendations: List[str] = Field(description="List of actionable recommendations.")
    severity: str = Field(default="Medium", description="Reported severity: Low, Medium, High, or Critical.")

def execute_structured_report(
    title: str,
    executive_summary: str,
    key_findings: List[str],
    recommendations: List[str],
    severity: str = "Medium"
) -> Dict[str, Any]:
    """Generates a formal, standardized enterprise markdown report."""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
    
    findings_md = "\n".join([f"- **Finding {idx+1}:** {f}" for idx, f in enumerate(key_findings)])
    recommendations_md = "\n".join([f"- [ ] **Action {idx+1}:** {r}" for idx, r in enumerate(recommendations)])

    markdown_report = (
        f"# 📋 Enterprise Technical Report: {title}\n"
        f"**Generated:** `{timestamp}` | **Classification:** Internal Enterprise | **Severity:** `{severity.upper()}`\n\n"
        f"## 1. Executive Summary\n{executive_summary}\n\n"
        f"## 2. Key Technical Findings & Evidence\n{findings_md}\n\n"
        f"## 3. Recommended Remediation Roadmap\n{recommendations_md}\n\n"
        f"---\n*Report generated automatically by Enterprise Intelligence Agent.*"
    )

    return {
        "title": title,
        "severity": severity,
        "markdown_report": markdown_report,
        "findings_count": len(key_findings),
        "recommendations_count": len(recommendations)
    }

# Tool Registry
TOOL_DEFINITIONS = [
    {
        "name": "knowledge_base_search",
        "description": "Searches the internal knowledge base for technical reports, error logs, architecture specs, and incident documents.",
        "parameters": KBSearchInput.model_json_schema()
    },
    {
        "name": "document_analysis",
        "description": "Performs in-depth analysis, pattern extraction, or root-cause identification on retrieved text or search findings.",
        "parameters": DocAnalysisInput.model_json_schema()
    },
    {
        "name": "structured_report_generator",
        "description": "Compiles analyzed findings and evidence into a formal, structured enterprise incident or audit report.",
        "parameters": ReportGenInput.model_json_schema()
    }
]
