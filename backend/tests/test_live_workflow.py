import asyncio
import os
import pytest
from app.services.ingestion.parsers import DocumentParser
from app.services.ingestion.chunker import RecursiveChunker
from app.services.retrieval.vector_store import vector_store
from app.services.retrieval.bm25_store import bm25_store
from app.services.retrieval.rag_engine import rag_engine
from app.services.agent.agent_runner import agent_runner

@pytest.mark.asyncio
async def test_live_indexing_and_rag_query():
    # 1. Ingest sample documents
    doc1_path = "../sample_data/architecture_specs.md"
    doc2_path = "../sample_data/incident_postmortem_db_pool.txt"
    
    sections1 = DocumentParser.parse(doc1_path, "md")
    sections2 = DocumentParser.parse(doc2_path, "txt")
    
    chunker = RecursiveChunker()
    chunks1 = chunker.chunk_document_sections(sections1, "doc_arch_1", "architecture_specs.md")
    chunks2 = chunker.chunk_document_sections(sections2, "doc_inc_2", "incident_postmortem_db_pool.txt")
    
    all_chunks = chunks1 + chunks2
    vector_store.add_chunks(all_chunks)
    bm25_store.add_chunks(all_chunks)
    
    print(f"\nIndexed {len(all_chunks)} chunks into vector and BM25 stores.")
    
    # 2. Test RAG query
    query = "What was the primary root cause of outage INC-89421 and what was the database connection pool limit?"
    result = await rag_engine.execute_query(query=query)
    
    print("\n--- RAG ANSWER ---")
    print(result["answer"])
    print("\n--- CITATIONS ---")
    for cit in result["citations"]:
        print(f"[{cit['document_name']} P.{cit['page_or_row']}]: {cit['excerpt'][:80]}...")
    print(f"Model used: {result['model_used']} via {result['provider_used']} (Latency: {result['latency_ms']}ms)")
    
    assert len(result["citations"]) > 0
    assert result["is_grounded"] is True
    assert "120" in result["answer"] or "pool" in result["answer"].lower()

@pytest.mark.asyncio
async def test_live_agent_multi_step_workflow():
    # The business scenario question from candidate brief:
    task = "Analyze our internal technical documentation and identify the most common reasons for system failures. Provide evidence from the documents and recommend possible solutions."
    
    agent_res = await agent_runner.execute_task(
        task=task,
        conversation_id="conv_test_agent",
        max_steps=5
    )
    
    print("\n================== AGENT MULTI-STEP EXECUTION TRACE ==================")
    for step in agent_res.steps:
        print(f"\n[Step {step.step_number}] Tool: {step.tool_name} (Status: {step.status}, Latency: {step.latency_ms}ms)")
        print(f"  Input: {step.tool_input}")
        print(f"  Output Summary: {str(step.tool_output)[:200]}...")
        
    print("\n================== FINAL AGENT ANSWER ==================")
    print(agent_res.final_output)
    
    assert agent_res.total_steps >= 2
    assert "knowledge_base_search" in agent_res.tools_used
