from typing import TypedDict, List, Dict, Any, Optional
import logging
from langgraph.graph import StateGraph, END
from agents.explorer import ExplorerAgent
from agents.proponent import ProponentAgent
from agents.skeptic import SkepticAgent
from agents.validator import ValidatorAgent
from core.types import RareAgentState

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Global Settings
MAX_HYPOTHESES = 5


# --- Agent Wrappers for Nodes ---

explorer = ExplorerAgent()
proponent = ProponentAgent()
skeptic = SkepticAgent()
validator = ValidatorAgent()

def explorer_node(state: RareAgentState):
    logger.info("--- Node: Explorer ---")
    return explorer.run(state)

def proponent_node(state: RareAgentState):
    logger.info("--- Node: Proponent ---")
    return proponent.run(state)

def skeptic_node(state: RareAgentState):
    logger.info("--- Node: Skeptic ---")
    return skeptic.run(state)

def validator_node(state: RareAgentState):
    logger.info("--- Node: Validator ---")
    return validator.run(state)

# --- Conditional Logic ---

def should_continue(state: RareAgentState):
    """
    Decides whether to loop back to Proponent or end.
    """
    hypotheses = state.get("hypotheses", [])
    retry_count = state.get("retry_count", 0)

    if not hypotheses:
        # If no hypothesis generated (e.g. no targets), end.
        logger.info("No hypotheses generated. Ending.")
        return END

    latest_hypothesis = hypotheses[-1]
    validation = latest_hypothesis.get("validation", {})
    skeptic_verdict = latest_hypothesis.get("skeptic_verdict", "UNKNOWN")
    
    # 1. Check Technical Validity (Validator)
    is_valid = validation.get("overall_status") == "APPROVED"
    
    # 2. Check Clinical Safety (Skeptic)
    is_safe = skeptic_verdict != "REJECT" and skeptic_verdict != "RISKY" # Strictness adjustable

    if is_valid and is_safe:
        logger.info("Hypothesis Approved and Safe. Finishing.")
        return END
    
    if retry_count < MAX_HYPOTHESES:
        logger.info(f"Hypothesis Rejected (Valid: {is_valid}, Safe: {is_safe}). Retrying ({retry_count + 1}/{MAX_HYPOTHESES})...")
        return "proponent"
    
    logger.info("Max hypotheses reached. Ending.")
    return END

# --- Build the Graph ---

def build_graph():
    workflow = StateGraph(RareAgentState)

    # Add Nodes
    workflow.add_node("explorer", explorer_node)
    workflow.add_node("proponent", proponent_node)
    workflow.add_node("skeptic", skeptic_node)
    workflow.add_node("validator", validator_node)

    # Set Entry Point
    workflow.set_entry_point("explorer")

    # Add Edges
    workflow.add_edge("explorer", "proponent")
    workflow.add_edge("proponent", "skeptic")
    workflow.add_edge("skeptic", "validator")
    
    # Conditional Edge from Validator
    workflow.add_conditional_edges(
        "validator",
        should_continue,
        {
            "proponent": "proponent",
            END: END
        }
    )

    app = workflow.compile()
    return app

# wrapper for UI streaming
def run_research(disease_name: str):
    """
    Runs the research workflow and yields state for UI updates.
    """
    app = build_graph()
    initial_state = {
        "current_disease": disease_name,
        "genetic_targets": [],
        "hypotheses": [],
        "evidence": [],
        "debate_history": [],
        "final_ranking": None,
        "retry_count": 0,
        "last_rejection_reason": None,
        "evaluated_drugs": []
    }
    
    # Stream events if possible, or just yield final
    # LangGraph .stream() yields events
    for event in app.stream(initial_state):
        yield event

if __name__ == "__main__":
    # Test Run
    print("Starting Orchestrator Test...")
    app = build_graph()
    result = app.invoke({
        "current_disease": "Cystic Fibrosis", 
        "retry_count": 0,
        "hypotheses": [],
        "debate_history": []
    })
    print("\nResult Keys:", result.keys())
    print("Hypotheses:", len(result.get("hypotheses", [])))
