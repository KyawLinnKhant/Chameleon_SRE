"""
Core agent logic using LangGraph
Implements a cyclic reasoning loop: Think → Act → Observe → Reflect
"""

import logging
from typing import Literal

from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

from .config import (
    OLLAMA_BASE_URL,
    MODEL_NAME,
    TEMPERATURE,
    MAX_ITERATIONS,
    SYSTEM_PROMPT
)
from .state import AgentState, should_continue
from .tools import get_tools

logger = logging.getLogger(__name__)


# ============================================================================
# LangGraph Nodes
# ============================================================================

def agent_node(state: AgentState) -> AgentState:
    """
    Main reasoning node where the agent thinks and decides what to do
    
    This node:
    1. Receives the current state
    2. Calls the LLM to decide next action
    3. Updates state with new messages
    """
    logger.info(f"Agent thinking (iteration {state['iteration_count']})...")
    
    # Initialize LLM with tool binding
    llm = ChatOllama(
        base_url=OLLAMA_BASE_URL,
        model=MODEL_NAME,
        temperature=TEMPERATURE
    )
    
    tools = get_tools()
    llm_with_tools = llm.bind_tools(tools)
    
    # Build message history
    messages = [SystemMessage(content=SYSTEM_PROMPT)] + state["messages"]
    
    # Add context from RAG if available
    if state["knowledge_context"]:
        context_msg = "\n\n".join([
            f"📚 Knowledge Base Context:\n{doc['content']}"
            for doc in state["knowledge_context"][:2]  # Top 2 results
        ])
        messages.append(SystemMessage(content=context_msg))
    
    # Call LLM
    try:
        response = llm_with_tools.invoke(messages)
        
        # Update state
        state["messages"].append(response)
        state["iteration_count"] += 1
        
        # Check if agent wants to finish
        if not response.tool_calls:
            # No more tools to call - task might be complete
            content = response.content.lower()
            if any(keyword in content for keyword in ["complete", "done", "finished", "resolved"]):
                state["task_complete"] = True
        
        return state
    
    except Exception as e:
        logger.error(f"Agent node error: {e}")
        state["error_log"].append(f"Agent reasoning failed: {str(e)}")
        state["messages"].append(AIMessage(
            content=f"I encountered an error while thinking: {str(e)}. Let me try a different approach."
        ))
        return state


def tool_node(state: AgentState) -> AgentState:
    """
    Execute tools requested by the agent
    
    This node:
    1. Extracts tool calls from last message
    2. Executes each tool
    3. Adds results back to state
    """
    logger.info("Executing tools...")
    
    last_message = state["messages"][-1]
    
    if not hasattr(last_message, "tool_calls") or not last_message.tool_calls:
        return state
    
    tools = {tool.name: tool for tool in get_tools()}
    
    for tool_call in last_message.tool_calls:
        tool_name = tool_call["name"]
        tool_args = tool_call["args"]
        
        logger.info(f"Calling tool: {tool_name} with args: {tool_args}")
        
        try:
            if tool_name in tools:
                result = tools[tool_name].invoke(tool_args)
                state["last_tool_output"] = result
                
                # Add tool result to messages
                state["messages"].append(ToolMessage(
                    content=str(result),
                    tool_call_id=tool_call["id"]
                ))
                
                # If it was a RAG search, store in knowledge context
                if tool_name == "read_rag_docs":
                    state["knowledge_context"].append({
                        "query": tool_args.get("query", ""),
                        "content": str(result)
                    })
            else:
                error_msg = f"Tool {tool_name} not found"
                logger.error(error_msg)
                state["error_log"].append(error_msg)
                state["messages"].append(ToolMessage(
                    content=f"ERROR: {error_msg}",
                    tool_call_id=tool_call["id"]
                ))
        
        except Exception as e:
            error_msg = f"Tool {tool_name} failed: {str(e)}"
            logger.error(error_msg)
            state["error_log"].append(error_msg)
            state["messages"].append(ToolMessage(
                content=f"ERROR: {error_msg}",
                tool_call_id=tool_call["id"]
            ))
    
    return state


# ============================================================================
# Routing Logic
# ============================================================================

def should_continue_routing(state: AgentState) -> Literal["tools", "end"]:
    """
    Determine if agent should continue to tools or end
    
    Returns:
        "tools" if there are tool calls to execute
        "end" if reasoning is complete
    """
    # Check iteration limit
    if not should_continue(state, MAX_ITERATIONS):
        logger.info("Reached max iterations or error limit")
        return "end"
    
    # Check if task is marked complete
    if state["task_complete"]:
        logger.info("Task marked as complete")
        return "end"
    
    # Check last message for tool calls
    last_message = state["messages"][-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    
    return "end"


# ============================================================================
# Graph Construction
# ============================================================================

def create_agent_graph():
    """
    Build the LangGraph state machine
    
    Graph structure:
        START → agent → [tools → agent] (loop) → END
    
    The agent can call tools, see results, and reason again in a loop
    """
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", tool_node)
    
    # Set entry point
    workflow.set_entry_point("agent")
    
    # Add conditional edges
    workflow.add_conditional_edges(
        "agent",
        should_continue_routing,
        {
            "tools": "tools",
            "end": END
        }
    )
    
    # Tools always go back to agent for reflection
    workflow.add_edge("tools", "agent")
    
    return workflow.compile()


# ============================================================================
# Agent Execution
# ============================================================================

def run_agent(user_input: str, verbose: bool = True) -> dict:
    """
    Run the agent on a user query
    
    Args:
        user_input: User's request
        verbose: Whether to print intermediate steps
    
    Returns:
        Final state dictionary
    """
    from .state import create_initial_state, format_state_for_display
    
    # Create graph
    graph = create_agent_graph()
    
    # Initialize state
    initial_state = create_initial_state(user_input)
    
    if verbose:
        print("\n🦎 Chameleon-SRE Agent Starting...")
        print("=" * 60)
    
    # Run graph
    final_state = None
    for state in graph.stream(initial_state):
        final_state = state
        if verbose and "agent" in state:
            print(format_state_for_display(state["agent"]))
    
    if verbose:
        print("\n✅ Agent Execution Complete")
        print("=" * 60)
    
    # Return the final state from the last key
    return list(final_state.values())[0] if final_state else initial_state


if __name__ == "__main__":
    # Test the agent
    logging.basicConfig(level=logging.INFO)
    
    test_query = "Check if there are any pods in CrashLoopBackOff state and fix them"
    result = run_agent(test_query)
    
    print("\n📋 Final Agent Response:")
    print(result["messages"][-1].content if result["messages"] else "No response")
