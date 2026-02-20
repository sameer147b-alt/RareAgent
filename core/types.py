from typing import TypedDict, List, Dict, Any, Optional

# Define the global state schema (Message Bus)
class RareAgentState(TypedDict):
    current_disease: str
    genetic_targets: List[Dict[str, Any]]
    hypotheses: List[Dict[str, Any]]
    evidence: List[Dict[str, Any]]
    debate_history: List[str]
    final_ranking: Optional[List[Dict[str, Any]]]
    retry_count: int
    last_rejection_reason: Optional[str]
    evaluated_drugs: List[str]
