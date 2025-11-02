"""Agent execution service with WebSocket streaming."""

import asyncio
import json
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langgraph.types import Command

from src.deep_agent import create_finance_deep_agent
from api import websocket as ws
from api.database import add_message, get_chat_messages, get_chat


# ============================================================================
# Agent Pool Management
# ============================================================================

class AgentPool:
    """Manages agent instances and execution state."""

    def __init__(self):
        self.agents: Dict[str, Any] = {}  # session_id -> agent
        self.pending_approvals: Dict[str, List] = {}  # chat_id -> approval data
        self.approval_futures: Dict[str, asyncio.Future] = {}  # chat_id -> future

    def get_or_create_agent(self, session_id: str, enable_hitl: bool = True):
        """Get existing agent or create new one."""
        if session_id not in self.agents:
            print(f"Creating new agent for session {session_id[:8]}...")
            self.agents[session_id] = create_finance_deep_agent(
                session_id=session_id,
                enable_human_in_loop=enable_hitl
            )
        return self.agents[session_id]

    def remove_agent(self, session_id: str):
        """Remove agent from pool."""
        if session_id in self.agents:
            del self.agents[session_id]

    def set_pending_approvals(self, chat_id: str, approvals: List):
        """Store pending approval requests."""
        self.pending_approvals[chat_id] = approvals

    def get_pending_approvals(self, chat_id: str) -> Optional[List]:
        """Get pending approval requests."""
        return self.pending_approvals.get(chat_id)

    def clear_pending_approvals(self, chat_id: str):
        """Clear pending approvals."""
        self.pending_approvals.pop(chat_id, None)

    def create_approval_future(self, chat_id: str) -> asyncio.Future:
        """Create a future for approval response."""
        future = asyncio.Future()
        self.approval_futures[chat_id] = future
        return future

    def resolve_approval_future(self, chat_id: str, decisions: List):
        """Resolve approval future with user decisions."""
        if chat_id in self.approval_futures:
            future = self.approval_futures.pop(chat_id)
            if not future.done():
                future.set_result(decisions)

    def cancel_approval_future(self, chat_id: str):
        """Cancel approval future."""
        if chat_id in self.approval_futures:
            future = self.approval_futures.pop(chat_id)
            if not future.done():
                future.cancel()


# Global agent pool
agent_pool = AgentPool()


# ============================================================================
# Helper Functions
# ============================================================================

def get_friendly_node_name(node_name: str) -> str:
    """Convert technical node names to user-friendly names."""
    name_map = {
        "PatchToolCallsMiddleware.before_agent": "Pre-processing",
        "SummarizationMiddleware.before_model": "Context Management",
        "model": "🤖 Main Agent",
        "tools": "Tool Execution",
    }
    return name_map.get(node_name, node_name)


def extract_subagent_name(node_name: str) -> Optional[str]:
    """Extract subagent name from node like 'SubAgent[market-data-fetcher]'."""
    if "[" in node_name and "]" in node_name:
        return node_name.split("[")[1].split("]")[0]
    return None


# ============================================================================
# Main Execution Function
# ============================================================================

async def execute_agent_stream(
    chat_id: str,
    user_message: str,
    session_id: str,
    enable_hitl: bool = True
) -> str:
    """
    Execute agent with streaming updates via WebSocket.

    Returns:
        message_id: ID of the AI response message
    """
    # Get or create agent
    agent = agent_pool.get_or_create_agent(session_id, enable_hitl)

    # Get chat data
    chat_data = get_chat(chat_id)
    if not chat_data:
        raise ValueError(f"Chat {chat_id} not found")

    # Create user message in DB
    user_msg_id = str(uuid.uuid4())
    add_message(
        message_id=user_msg_id,
        chat_id=chat_id,
        role="user",
        content=user_message
    )

    # Send start event
    ai_msg_id = str(uuid.uuid4())
    await ws.send_start_event(chat_id, ai_msg_id)

    # Get conversation history
    db_messages = get_chat_messages(chat_id)
    conversation_messages = []

    for msg in db_messages:
        if msg["role"] == "user":
            conversation_messages.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            conversation_messages.append(AIMessage(content=msg["content"]))

    # Prepare state
    state = {
        "messages": conversation_messages,
        "files": {}
    }
    config = {
        "configurable": {
            "thread_id": session_id
        }
    }

    # Execute agent with streaming
    step_count = 0
    new_messages = []
    files = {}
    todos = []
    has_interrupted = False
    collected_interrupts = []

    try:
        async for chunk in agent.astream(state, config=config, stream_mode="updates"):
            step_count += 1

            for node_name, state_update in chunk.items():
                # Check for interrupts
                if node_name == "__interrupt__":
                    has_interrupted = True
                    if isinstance(state_update, (tuple, list)):
                        collected_interrupts.extend(state_update)
                    else:
                        collected_interrupts.append(state_update)
                    continue

                # Detect subagent
                is_subagent = "SubAgent" in node_name
                subagent_name = extract_subagent_name(node_name) if is_subagent else None
                friendly_name = get_friendly_node_name(node_name)

                # Send step event
                await ws.send_step_event(
                    chat_id=chat_id,
                    step_number=step_count,
                    node_name=node_name,
                    friendly_name=friendly_name,
                    is_subagent=is_subagent,
                    subagent_name=subagent_name
                )

                if state_update is None:
                    continue

                # Process messages
                if "messages" in state_update:
                    messages = state_update["messages"]
                    if hasattr(messages, "value"):  # Unwrap Overwrite
                        messages = messages.value
                    if not isinstance(messages, (list, tuple)):
                        messages = [messages]

                    for msg in messages:
                        new_messages.append(msg)

                        # Tool calls
                        if msg.type == "ai" and hasattr(msg, "tool_calls") and msg.tool_calls:
                            for tool_call in msg.tool_calls:
                                await ws.send_tool_call_event(
                                    chat_id=chat_id,
                                    tool_call_id=tool_call.get("id", str(uuid.uuid4())),
                                    name=tool_call.get("name", "unknown"),
                                    args=tool_call.get("args", {}),
                                    is_subagent=is_subagent
                                )

                        # Tool results
                        elif msg.type == "tool":
                            tool_name = getattr(msg, 'name', 'unknown')
                            content = msg.content

                            # Try to parse content as JSON
                            try:
                                if isinstance(content, str):
                                    result = json.loads(content)
                                else:
                                    result = content
                                success = result.get("success", True) if isinstance(result, dict) else True
                                error = result.get("error") if isinstance(result, dict) else None
                            except:
                                result = content
                                success = True
                                error = None

                            await ws.send_tool_result_event(
                                chat_id=chat_id,
                                tool_call_id=getattr(msg, 'tool_call_id', str(uuid.uuid4())),
                                name=tool_name,
                                result=result,
                                success=success,
                                error=error,
                                is_subagent=is_subagent
                            )

                # Process file updates
                if "files" in state_update and state_update["files"]:
                    new_files = state_update["files"]
                    if hasattr(new_files, "value"):
                        new_files = new_files.value

                    changed_files = []
                    for path, data in new_files.items():
                        if path not in files or files[path] != data:
                            changed_files.append(path)
                    files.update(new_files)

                    if changed_files:
                        await ws.send_file_update_event(chat_id, changed_files)

                # Process todos
                if "todos" in state_update and state_update["todos"]:
                    new_todos = state_update["todos"]
                    if hasattr(new_todos, "value"):
                        new_todos = new_todos.value
                    todos = new_todos
                    await ws.send_todo_update_event(chat_id, todos)

        # Handle interrupts (approvals)
        if has_interrupted and collected_interrupts:
            # Extract approval requests
            all_action_requests = []
            all_review_configs = []

            for interrupt in collected_interrupts:
                interrupt_data = interrupt.value if hasattr(interrupt, 'value') else interrupt

                if isinstance(interrupt_data, dict):
                    action_requests = interrupt_data.get("action_requests", [])
                    review_configs = interrupt_data.get("review_configs", [])
                    all_action_requests.extend(action_requests)
                    all_review_configs.extend(review_configs)

            # Build approval requests
            config_map = {cfg.get("action_name", ""): cfg for cfg in all_review_configs if cfg.get("action_name")}
            approval_requests = []

            for action_request in all_action_requests:
                tool_name = action_request.get("name", "unknown")
                review_config = config_map.get(tool_name, {"allowed_decisions": ["approve", "reject"]})
                approval_requests.append({
                    "action_request": action_request,
                    "review_config": review_config
                })

            # Store pending approvals
            agent_pool.set_pending_approvals(chat_id, approval_requests)

            # Send approval request event
            await ws.send_approval_request_event(chat_id, approval_requests)

            # Wait for approval response
            approval_future = agent_pool.create_approval_future(chat_id)

            try:
                # Wait up to 5 minutes for approval
                decisions = await asyncio.wait_for(approval_future, timeout=300)
            except asyncio.TimeoutError:
                await ws.send_error_event(chat_id, "Approval timeout", "No response received within 5 minutes")
                agent_pool.clear_pending_approvals(chat_id)
                raise

            # Clear pending approvals
            agent_pool.clear_pending_approvals(chat_id)

            # Resume execution with decisions
            resume_state = Command(resume={"decisions": decisions})

            # Stream resumed execution
            async for chunk in agent.astream(resume_state, config=config, stream_mode="updates"):
                step_count += 1

                for node_name, state_update in chunk.items():
                    is_subagent = "SubAgent" in node_name
                    subagent_name = extract_subagent_name(node_name) if is_subagent else None
                    friendly_name = get_friendly_node_name(node_name)

                    await ws.send_step_event(
                        chat_id=chat_id,
                        step_number=step_count,
                        node_name=node_name,
                        friendly_name=friendly_name,
                        is_subagent=is_subagent,
                        subagent_name=subagent_name
                    )

                    if state_update is None:
                        continue

                    # Same processing as above for messages, files, todos
                    if "messages" in state_update:
                        messages = state_update["messages"]
                        if hasattr(messages, "value"):
                            messages = messages.value
                        if not isinstance(messages, (list, tuple)):
                            messages = [messages]

                        for msg in messages:
                            new_messages.append(msg)

                            if msg.type == "ai" and hasattr(msg, "tool_calls") and msg.tool_calls:
                                for tool_call in msg.tool_calls:
                                    await ws.send_tool_call_event(
                                        chat_id=chat_id,
                                        tool_call_id=tool_call.get("id", str(uuid.uuid4())),
                                        name=tool_call.get("name", "unknown"),
                                        args=tool_call.get("args", {}),
                                        is_subagent=is_subagent
                                    )

                            elif msg.type == "tool":
                                tool_name = getattr(msg, 'name', 'unknown')
                                content = msg.content
                                try:
                                    result = json.loads(content) if isinstance(content, str) else content
                                    success = result.get("success", True) if isinstance(result, dict) else True
                                    error = result.get("error") if isinstance(result, dict) else None
                                except:
                                    result = content
                                    success = True
                                    error = None

                                await ws.send_tool_result_event(
                                    chat_id=chat_id,
                                    tool_call_id=getattr(msg, 'tool_call_id', str(uuid.uuid4())),
                                    name=tool_name,
                                    result=result,
                                    success=success,
                                    error=error,
                                    is_subagent=is_subagent
                                )

                    if "files" in state_update and state_update["files"]:
                        new_files = state_update["files"]
                        if hasattr(new_files, "value"):
                            new_files = new_files.value
                        changed_files = []
                        for path, data in new_files.items():
                            if path not in files or files[path] != data:
                                changed_files.append(path)
                        files.update(new_files)
                        if changed_files:
                            await ws.send_file_update_event(chat_id, changed_files)

                    if "todos" in state_update and state_update["todos"]:
                        new_todos = state_update["todos"]
                        if hasattr(new_todos, "value"):
                            new_todos = new_todos.value
                        todos = new_todos
                        await ws.send_todo_update_event(chat_id, todos)

        # Get final AI response
        ai_messages = [m for m in new_messages if m.type == "ai"]
        final_response = ai_messages[-1].content if ai_messages else "No response generated"

        # Save AI message to DB
        add_message(
            message_id=ai_msg_id,
            chat_id=chat_id,
            role="assistant",
            content=final_response
        )

        # Send complete event
        await ws.send_complete_event(chat_id, {
            "id": ai_msg_id,
            "role": "assistant",
            "content": final_response,
            "created_at": datetime.now().isoformat()
        })

        return ai_msg_id

    except Exception as e:
        # Send error event
        await ws.send_error_event(chat_id, str(e), None)
        raise


# ============================================================================
# Approval Response Handler
# ============================================================================

def handle_approval_response(chat_id: str, decisions: List[Dict]):
    """Handle user's approval response."""
    agent_pool.resolve_approval_future(chat_id, decisions)
