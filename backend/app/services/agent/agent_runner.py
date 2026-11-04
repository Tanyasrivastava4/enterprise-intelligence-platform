import time
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from pydantic import ValidationError

from app.services.llm.fallback_router import llm_router
from app.services.agent.tools import (
    TOOL_DEFINITIONS,
    KBSearchInput, execute_kb_search,
    DocAnalysisInput, execute_doc_analysis,
    ReportGenInput, execute_structured_report
)
from app.schemas.agent import AgentExecutionStep, AgentTaskResponse
from app.core.config import settings

logger = logging.getLogger("agent_runner")

AGENT_SYSTEM_PROMPT = """You are an Autonomous AI Enterprise Intelligence Agent.
You assist employees and leadership by investigating complex questions across internal company records, analyzing technical documentation, and generating actionable executive reports.

You have access to the following approved tools:
1. `knowledge_base_search`: Searches internal documents for evidence. Arguments: {"query": str, "top_k": int, "document_name_filter": Optional[str]}
2. `document_analysis`: Analyzes retrieved text or search findings to extract root causes and patterns. Arguments: {"target_content": str, "analysis_focus": str}
3. `structured_report_generator`: Compiles verified findings into a formal report. Arguments: {"title": str, "executive_summary": str, "key_findings": List[str], "recommendations": List[str], "severity": str}

CRITICAL OPERATIONAL RULES:
- When a user asks a complex multi-step question (such as analyzing failure causes and recommending solutions):
  Step 1: First search internal documents via `knowledge_base_search`.
  Step 2: Take the search output and analyze it using `document_analysis`.
  Step 3: Compile the final findings and recommendations into `structured_report_generator`.
- Always output your reasoning and tool decision strictly in valid JSON format:
```json
{
  "thought": "Explain your chain of thought and why you chose this action",
  "action": "call_tool",
  "tool_name": "knowledge_base_search",
  "tool_args": {"query": "system failure logs and root causes", "top_k": 4}
}
```
Or when all required steps are complete:
```json
{
  "thought": "I have collected the evidence, analyzed the patterns, and compiled the formal report.",
  "action": "finish",
  "final_answer": "Complete textual answer summarizing the findings with source references",
  "structured_report": { ...optional report object if generated... }
}
```
NEVER output raw conversational text outside the JSON code block.
"""

class AgentRunner:

    async def execute_task(
        self,
        task: str,
        conversation_id: str,
        max_steps: int = settings.AGENT_MAX_ITERATIONS
    ) -> AgentTaskResponse:
        start_time = time.time()
        steps: List[AgentExecutionStep] = []
        tools_used: List[str] = []
        
        step_number = 1
        intermediate_history: List[str] = []
        total_tokens = 0
        last_model = settings.GROQ_MODEL
        last_provider = "groq"
        is_fallback_triggered = False
        final_answer = ""
        structured_report = None

        while step_number <= max_steps:
            # Check timeout guardrail
            if (time.time() - start_time) > settings.AGENT_TIMEOUT_SECONDS:
                logger.warning(f"Agent exceeded timeout threshold of {settings.AGENT_TIMEOUT_SECONDS}s")
                final_answer = "Execution reached maximum time budget. Summary of steps completed so far:\n" + "\n".join(intermediate_history)
                break

            # Construct iteration prompt
            history_text = "\n\n".join(intermediate_history) if intermediate_history else "No prior tool steps executed yet."
            iteration_prompt = (
                f"User Goal: {task}\n\n"
                f"History of Actions Executed So Far:\n{history_text}\n\n"
                f"Current Step: {step_number}/{max_steps}\n"
                f"What is your next action? Respond in valid JSON."
            )

            llm_res = await llm_router.generate_with_fallback(
                prompt=iteration_prompt,
                system_prompt=AGENT_SYSTEM_PROMPT,
                temperature=0.1,
                max_tokens=1000
            )

            total_tokens += llm_res.total_tokens
            last_model = llm_res.model
            last_provider = llm_res.provider
            if llm_res.is_fallback:
                is_fallback_triggered = True

            # Parse model output JSON
            parsed_decision = self._parse_json_decision(llm_res.content)
            action = parsed_decision.get("action", "finish")
            thought = parsed_decision.get("thought", "")

            if action == "finish":
                final_answer = parsed_decision.get("final_answer", llm_res.content)
                structured_report = parsed_decision.get("structured_report")
                break

            elif action == "call_tool":
                tool_name = parsed_decision.get("tool_name")
                tool_args = parsed_decision.get("tool_args", {})
                
                tool_start = time.time()
                tool_output, tool_status = await self._execute_tool_safe(tool_name, tool_args)
                tool_latency = int((time.time() - tool_start) * 1000)

                # Record execution step
                step = AgentExecutionStep(
                    step_number=step_number,
                    tool_name=tool_name,
                    tool_input=tool_args,
                    tool_output=tool_output,
                    latency_ms=tool_latency,
                    status=tool_status
                )
                steps.append(step)
                if tool_name not in tools_used:
                    tools_used.append(tool_name)

                # Record in intermediate context for next iteration
                step_summary = (
                    f"Step {step_number}: Called '{tool_name}' with args {json.dumps(tool_args)}.\n"
                    f"Result: {json.dumps(tool_output)[:1200]}"
                )
                intermediate_history.append(step_summary)
                
                # If report was generated, store reference
                if tool_name == "structured_report_generator" and tool_status == "success":
                    structured_report = tool_output

                step_number += 1

            else:
                # Unrecognized action, treat as finish
                final_answer = llm_res.content
                break

        if not final_answer:
            final_answer = "Multi-step agent workflow completed successfully."

        total_latency = int((time.time() - start_time) * 1000)

        return AgentTaskResponse(
            conversation_id=conversation_id,
            task=task,
            final_output=final_answer,
            structured_report=structured_report,
            steps=steps,
            tools_used=tools_used,
            total_steps=len(steps),
            total_latency_ms=total_latency,
            total_tokens=total_tokens,
            model_used=last_model,
            provider_used=last_provider,
            is_fallback=is_fallback_triggered,
            created_at=time.strftime("%Y-%m-%d %H:%M:%S")
        )

    def _parse_json_decision(self, content: str) -> Dict[str, Any]:
        """Extracts JSON object from model output."""
        try:
            # First try direct parse
            return json.loads(content.strip())
        except Exception:
            # Look for markdown code fence
            import re
            json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", content, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group(1))
                except Exception:
                    pass
            
            # Look for bare brackets
            brace_match = re.search(r"\{.*\}", content, re.DOTALL)
            if brace_match:
                try:
                    return json.loads(brace_match.group(0))
                except Exception:
                    pass

        # Fallback if model returned plain text
        return {
            "action": "finish",
            "thought": "Direct response generated",
            "final_answer": content
        }

    async def _execute_tool_safe(self, tool_name: str, tool_args: Dict[str, Any]) -> Tuple[Any, str]:
        """Validates tool parameters with Pydantic and executes tool safely."""
        try:
            if tool_name == "knowledge_base_search":
                validated = KBSearchInput(**tool_args)
                result = execute_kb_search(
                    query=validated.query,
                    top_k=validated.top_k,
                    document_name_filter=validated.document_name_filter
                )
                return result, "success"

            elif tool_name == "document_analysis":
                validated = DocAnalysisInput(**tool_args)
                result = await execute_doc_analysis(
                    target_content=validated.target_content,
                    analysis_focus=validated.analysis_focus
                )
                return result, "success"

            elif tool_name == "structured_report_generator":
                validated = ReportGenInput(**tool_args)
                result = execute_structured_report(
                    title=validated.title,
                    executive_summary=validated.executive_summary,
                    key_findings=validated.key_findings,
                    recommendations=validated.recommendations,
                    severity=validated.severity
                )
                return result, "success"

            else:
                return {"error": f"Unknown tool: '{tool_name}'"}, "error"

        except ValidationError as val_err:
            return {"validation_error": str(val_err)}, "error"
        except Exception as exec_err:
            return {"execution_error": str(exec_err)}, "error"

agent_runner = AgentRunner()
