from typing import List, Optional
from pydantic import BaseModel
from app.agent.planner import plan_task, ChatMessage
from app.tools.registry import registry

class AgentResponse(BaseModel):
    status: str
    output: str
    reasoning_trace: str
    tool_used: Optional[str] = None

class AgentExecutor:
    @staticmethod
    async def run(user_query: str, extracted_text: str = "", history: List[ChatMessage] = []) -> AgentResponse:
        # 1. Determine action plan
        try:
            plan = await plan_task(user_query, extracted_text, history)
        except Exception as e:
            return AgentResponse(
                status="error",
                output=f"Planning stage failed: {str(e)}",
                reasoning_trace="Failed to analyze user intent."
            )

        # 2. Handle clarification requests
        if not plan.is_clear:
            return AgentResponse(
                status="clarify",
                output=plan.follow_up_question or "Could you clarify what you would like me to do?",
                reasoning_trace=plan.reasoning
            )

        tool = registry.get_tool(plan.selected_tool)
        if not tool:
            return AgentResponse(
                status="error",
                output=f"Tool '{plan.selected_tool}' is not registered.",
                reasoning_trace=plan.reasoning
            )

        # 3. Package conversational history into the execution context
        execution_context = {"history": history}

        try:
            payload = extracted_text if extracted_text else user_query
            
            # Run the tool with context awareness
            result = await tool.execute(payload, context=execution_context)
            
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