"""
Simplified agent - executes one action and stops.
Much faster for simple queries.
"""

from typing import Literal
import re
import warnings

warnings.filterwarnings('ignore', category=DeprecationWarning)

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, END
from loguru import logger

from src.config import settings
from src.state import AgentState, create_initial_state
from src.tools import (
    execute_k8s_command,
    get_pod_status,
    read_pod_logs,
    describe_resource,
    read_rag_docs
)
from src.utils import setup_logging
from models.ollama_client import get_llm


SIMPLE_PROMPT = """You are Chameleon-SRE, a Kubernetes assistant.

When the user asks a question, you will:
1. Execute ONE action to get the information
2. Analyze the result
3. Give a brief answer
4. STOP (do not execute more actions unless there's an error)

Actions (use EXACTLY this format):
ACTION: kubectl
INPUT: get pods

ACTION: describe  
INPUT: pod nginx default

ACTION: logs
INPUT: nginx default

ACTION: search_docs
INPUT: what causes ImagePullBackOff

CRITICAL: After you see OBSERVATION with results, immediately provide your FINAL ANSWER. Do NOT execute another action unless the first one failed.
"""


def parse_action(text: str) -> tuple[str | None, str | None]:
    """Parse ACTION and INPUT."""
    action_match = re.search(r'ACTION:\s*(.+?)(?:\n|$)', text, re.IGNORECASE)
    if not action_match:
        return None, None
    
    action = action_match.group(1).strip()
    input_match = re.search(r'INPUT:\s*(.+?)(?:\n|OBSERVATION|$)', text, re.IGNORECASE | re.DOTALL)
    input_text = input_match.group(1).strip() if input_match else ""
    
    return action, input_text


def execute_action(action: str, input_text: str) -> str:
    """Execute action."""
    try:
        action_lower = action.lower()
        
        if action_lower == 'kubectl':
            full_command = f"kubectl {input_text}" if input_text else "kubectl get pods"
            logger.info(f"Executing: {full_command}")
            return execute_k8s_command.invoke({"command": full_command})
            
        elif action_lower in ['describe', 'describe_resource']:
            parts = input_text.split()
            if len(parts) < 2:
                return "❌ Format: describe <type> <name> [namespace]"
            return describe_resource.invoke({
                "resource_type": parts[0],
                "resource_name": parts[1],
                "namespace": parts[2] if len(parts) > 2 else "default"
            })
            
        elif action_lower in ['logs', 'read_logs']:
            parts = input_text.split()
            if not parts:
                return "❌ Format: logs <pod-name> [namespace]"
            return read_pod_logs.invoke({
                "pod_name": parts[0],
                "namespace": parts[1] if len(parts) > 1 else "default",
                "tail": 50
            })
            
        elif action_lower in ['search_docs', 'docs']:
            return read_rag_docs.invoke({"query": input_text or "kubernetes"})
            
        else:
            return f"❌ Unknown action. Use: kubectl, describe, logs, search_docs"
        
    except Exception as e:
        return f"❌ Error: {e}"


def create_simple_graph() -> StateGraph:
    """Create simple graph."""
    
    graph = StateGraph(AgentState)
    llm = get_llm()
    
    def agent_node(state: AgentState) -> AgentState:
        """Agent node."""
        iteration = state["iteration_count"]
        
        # First iteration - execute action
        if iteration == 0:
            messages = [SystemMessage(content=SIMPLE_PROMPT)] + state["messages"]
            response = llm.invoke(messages)
            
            action, input_params = parse_action(response.content)
            
            if action:
                logger.info(f"Action: {action} {input_params}")
                observation = execute_action(action, input_params)
                
                # Ask for final answer
                obs_msg = HumanMessage(
                    content=f"OBSERVATION: {observation}\n\nProvide your final answer now (do not execute more actions)."
                )
                
                return {
                    **state,
                    "messages": [response, obs_msg],
                    "iteration_count": 1,
                }
            else:
                # No action needed, direct answer
                return {
                    **state,
                    "messages": [response],
                    "iteration_count": 1,
                    "task_completed": True,
                }
        
        # Second iteration - final answer only
        else:
            messages = [SystemMessage(content=SIMPLE_PROMPT)] + state["messages"]
            response = llm.invoke(messages)
            
            return {
                **state,
                "messages": [response],
                "iteration_count": 2,
                "task_completed": True,
            }
    
    def should_continue(state: AgentState) -> Literal["agent", "end"]:
        """Check if done."""
        if state.get("task_completed", False):
            return "end"
        if state["iteration_count"] >= 2:  # Max 2 iterations
            return "end"
        return "agent"
    
    graph.add_node("agent", agent_node)
    graph.set_entry_point("agent")
    graph.add_conditional_edges("agent", should_continue, {"agent": "agent", "end": END})
    
    return graph.compile()


def run_agent(user_input: str, namespace: str = "default") -> str:
    """Run agent."""
    logger.info(f"Query: {user_input}")
    
    state = create_initial_state(namespace)
    state["messages"] = [HumanMessage(content=user_input)]
    
    graph = create_simple_graph()
    final_state = graph.invoke(state)
    
    # Get last AI message
    for msg in reversed(final_state.get("messages", [])):
        if isinstance(msg, AIMessage):
            text = msg.content
            # Remove ACTION/INPUT from output
            text = re.sub(r'^ACTION:.*$', '', text, flags=re.MULTILINE | re.IGNORECASE)
            text = re.sub(r'^INPUT:.*$', '', text, flags=re.MULTILINE | re.IGNORECASE)
            cleaned = text.strip()
            return cleaned if cleaned else msg.content
    
    return "❌ No response"


def interactive_mode():
    """CLI mode."""
    print("🦎 Chameleon-SRE (Fast Mode)")
    print("=" * 60)
    print("Simple queries only - one action per question")
    print("Type 'exit' to quit.")
    print("=" * 60)
    print()
    
    namespace = input("Kubernetes namespace (default: 'default'): ").strip() or "default"
    print(f"Operating in namespace: {namespace}\n")
    
    while True:
        try:
            user_input = input("\n🔧 You: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ["exit", "quit", "q"]:
                print("👋 Goodbye!")
                break
            
            print("\n🦎 Chameleon-SRE:")
            response = run_agent(user_input, namespace)
            print(response)
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            logger.error(f"Error: {e}")
            print(f"❌ Error: {e}")


def main():
    """Entry point."""
    setup_logging(verbose=settings.verbose)
    logger.info("🦎 Chameleon-SRE (Fast Mode) Starting")
    logger.info(f"Model: {settings.ollama_model}")
    interactive_mode()


if __name__ == "__main__":
    main()