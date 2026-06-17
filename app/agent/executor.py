from typing import List, Dict, Any, Optional
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
        # Pass history to help resolve follow-up replies
        try:
            plan = await plan_task(user_query, extracted_text, history)
        except Exception as e:
            return AgentResponse(
                status="error",
                output=f"Planning stage failed: {str(e)}",
                reasoning_trace="Failed to analyze user intent."
            )

        if not plan.is_clear:
            return AgentResponse(
                status="clarify",
                output=plan.follow_up_question or "Could you clarify what you would like me to do with this input?",
                reasoning_trace=plan.reasoning
            )

        tool = registry.get_tool(plan.selected_tool)
        if not tool:
            return AgentResponse(
                status="error",
                output=f"Tool '{plan.selected_tool}' was planned but is not registered.",
                reasoning_trace=plan.reasoning
            )

        try:
            # If the user is responding to code previously sent, find that context
            payload = extracted_text if extracted_text else user_query
            if not payload and history:
                # Fallback to search past user inputs if current payload is brief response
                for msg in reversed(history):
                    if msg.role == "user" and len(msg.content) > 10:
                        payload = msg.content
                        break
            
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