from typing import Dict, Any
from pydantic import BaseModel
from app.agent.planner import plan_task
from app.tools.registry import registry

class AgentResponse(BaseModel):
    status: str  # "clarify" or "success" or "error"
    output: str
    reasoning_trace: str
    tool_used: str = None

class AgentExecutor:
    @staticmethod
    async def run(user_query: str, extracted_text: str = "") -> AgentResponse:
        # Step 1: Detect intent and construct plan
        try:
            plan = await plan_task(user_query, extracted_text)
        except Exception as e:
            return AgentResponse(
                status="error",
                output=f"Planning stage failed: {str(e)}",
                reasoning_trace="Failed to analyze user intent."
            )

        # Step 2: Handle ambiguity (Mandatory Follow-up Question rule)
        if not plan.is_clear:
            return AgentResponse(
                status="clarify",
                output=plan.follow_up_question or "Could you clarify what you would like me to do with this input?",
                reasoning_trace=plan.reasoning
            )

        # Step 3: Run the selected tool
        tool = registry.get_tool(plan.selected_tool)
        if not tool:
            return AgentResponse(
                status="error",
                output=f"Tool '{plan.selected_tool}' was planned but is not registered.",
                reasoning_trace=plan.reasoning
            )

        try:
            # For now, pass whichever input content holds the payload
            payload = extracted_text if extracted_text else user_query
            result = await tool.execute(payload)
            return AgentResponse(
                status="success",
                output=result,
                reasoning_trace=f"Planner reasoning: {plan.reasoning}\nExecuted tool: {tool.name}",
                tool_used=tool.name
            )
        except Exception as e:
            return AgentResponse(
                status="error",
                output=f"Execution error while running {tool.name}: {str(e)}",
                reasoning_trace=plan.reasoning,
                tool_used=tool.name
            )